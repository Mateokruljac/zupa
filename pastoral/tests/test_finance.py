from django.test import RequestFactory, SimpleTestCase

from pastoral.services.cashbook import cashbook_page_context
from pastoral.services.finance_reports import finance_reports_context
from pastoral.services.invoices_page import invoices_page_context


class FinanceContextTests(SimpleTestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.parish_data = {
            'cashbook': [
                {
                    'date': '2026-01-10',
                    'type': 'ulaz',
                    'ledger': 'plavi',
                    'category': 'lukno',
                    'description': 'Lukno',
                    'paymentMethod': 'gotovina',
                    'amount': 200,
                },
                {
                    'date': '2026-01-11',
                    'type': 'izlaz',
                    'ledger': 'plavi',
                    'category': 'režije',
                    'description': 'Struja',
                    'paymentMethod': 'račun',
                    'amount': 75,
                },
            ],
            'invoices': [
                {
                    'id': 'invoice-1',
                    'direction': 'incoming',
                    'issueDate': '2026-01-11',
                    'dueDate': '2026-02-01',
                    'total': 75,
                    'paidAmount': 0,
                    'status': 'primljen',
                },
            ],
            'parishDebts': [
                {
                    'id': 'debt-1',
                    'direction': 'payable',
                    'label': 'Popravak krova',
                    'category': 'dobavljaci',
                    'amount': 500,
                    'dueDate': '2026-02-01',
                    'paid': False,
                },
            ],
        }

    def test_finance_overview_contains_only_real_financial_totals(self):
        request = self.request_factory.get('/pages/financijska-izvjestaja/', {
            'year': '2026',
        })

        context = finance_reports_context(self.parish_data, request)

        self.assertEqual(context['year_summary']['in_sum'], 200)
        self.assertEqual(context['year_summary']['out_sum'], 75)
        self.assertEqual(context['year_summary']['balance'], 125)
        self.assertEqual(context['invoice_summary']['unpaid_sum'], 75)
        self.assertEqual(context['finance_obligations']['payable_sum'], 500)
        self.assertNotIn('report_health', context)
        self.assertNotIn('quarter_rows', context)

    def test_cashbook_filter_does_not_change_yearly_summary(self):
        request = self.request_factory.get('/pages/blagajna/', {
            'year': '2026',
            'ledger': 'crveni',
        })

        context = cashbook_page_context(self.parish_data, request)

        self.assertEqual(context['cashbook_rows'], [])
        self.assertEqual(context['cashbook_summary']['balance'], 125)

    def test_invoice_summary_reports_open_amount(self):
        request = self.request_factory.get('/pages/racuni/', {
            'year': '2026',
        })

        context = invoices_page_context(self.parish_data, request)

        self.assertEqual(context['invoice_summary']['open'], 1)
        self.assertEqual(context['invoice_summary']['unpaid_sum'], 75)
        self.assertEqual(context['invoice_summary']['overdue'], 1)
        self.assertTrue(context['invoice_rows'][0]['is_overdue'])
