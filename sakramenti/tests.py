from datetime import date
from django.test import SimpleTestCase
from isprave.forms import BaptismRegistryForm, FuneralRegistryForm, MarriageRegistryForm, RegistryBookForm
from isprave.models import RegisterBook
from isprave.services.registry_books import REGISTRY_TYPE_PRESENTATION
from sakramenti.models import BaptismDetails, FuneralDetails, MarriageDetails


def valid_baptism_form_data(**overrides):
    data = {
        'entry_number': '1',
        'birth_date': '2020-01-10',
        'baptism_date': '2020-02-10',
        'child_first_name': 'Ana',
        'child_last_name': 'Horvat',
        'child_sex': 'daughter',
        'baptism_place': 'Zagreb',
        'identifier_type': '',
        'identifier_value': '',
        'father_first_name': 'Ivan',
        'father_last_name': 'Horvat',
        'father_religion': 'Katolička',
        'mother_first_name': 'Marija',
        'mother_last_name': 'Horvat',
        'mother_religion': 'Katolička',
        'parents_canonically_married': 'True',
        'residence_address': 'Ilica 1, Zagreb',
        'godparent_first_name': 'Petra',
        'godparent_last_name': 'Marić',
        'minister_first_name': 'Marko',
        'minister_last_name': 'Kovač',
        'minister_role': 'župnik',
        'status': 'upis',
        'stipend': '0',
    }
    data.update(overrides)
    return data


class BaptismRegistryFormTests(SimpleTestCase):
    def test_confirmation_register_cannot_be_created(self):
        available_types = {
            value for value, _label in RegistryBookForm.base_fields['book_type'].choices
        }

        self.assertNotIn('krizma', available_types)
        self.assertNotIn('krizma', RegisterBook.RegistryType.values)
        self.assertNotIn('krizma', REGISTRY_TYPE_PRESENTATION)

    def test_future_annotations_and_identifier_are_optional(self):
        form = BaptismRegistryForm(valid_baptism_form_data(), selected_year=2020)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.cleaned_data['parents_canonically_married'])

    def test_baptism_cannot_precede_birth(self):
        form = BaptismRegistryForm(
            valid_baptism_form_data(baptism_date='2019-12-31'),
            selected_year=2020,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('baptism_date', form.errors)

    def test_identifier_type_and_value_are_validated_together(self):
        form = BaptismRegistryForm(
            valid_baptism_form_data(
                identifier_type='oib', identifier_value='123'
            ),
            selected_year=2020,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('identifier_value', form.errors)


class BaptismContentHashTests(SimpleTestCase):
    def test_hash_is_deterministic_and_changes_with_business_content(self):
        record = BaptismDetails(
            birth_date=date(2020, 1, 10),
            baptism_date=date(2020, 2, 10),
            child_first_name='Ana',
            child_last_name='Horvat',
        )
        first_hash = record.calculate_content_hash()

        self.assertEqual(first_hash, record.calculate_content_hash())
        self.assertEqual(len(first_hash), 64)

        record.notes = 'Naknadni upis'
        self.assertNotEqual(first_hash, record.calculate_content_hash())


def valid_funeral_form_data(**overrides):
    data = {
        'entry_number': '1', 'physical_page': '12',
        'death_date': '2020-02-10', 'death_place': 'Zagreb',
        'first_name': 'Ivan', 'last_name': 'Horvat', 'sex': 'male',
        'birth_place': 'Split', 'birth_date': '1940-01-10',
        'identifier_type': '', 'identifier_value': '',
        'spouse_first_name': '', 'spouse_last_name': '',
        'father_first_name': 'Marko', 'father_last_name': 'Horvat',
        'mother_first_name': 'Ana', 'mother_last_name': 'Marić',
        'residence_address': 'Ilica 1, Zagreb',
        'burial_place': 'Mirogoj', 'burial_date': '2020-02-12',
        'minister_first_name': 'Petar', 'minister_last_name': 'Kovač',
        'cause_of_death': '', 'notes': '',
    }
    data.update(overrides)
    return data


class FuneralRegistryFormTests(SimpleTestCase):
    def test_optional_identifier_spouse_and_cause_are_accepted(self):
        form = FuneralRegistryForm(valid_funeral_form_data(), selected_year=2020)
        self.assertTrue(form.is_valid(), form.errors)

    def test_death_cannot_precede_birth(self):
        form = FuneralRegistryForm(
            valid_funeral_form_data(birth_date='2021-01-01'), selected_year=2020
        )
        self.assertFalse(form.is_valid())
        self.assertIn('death_date', form.errors)

    def test_burial_cannot_precede_death(self):
        form = FuneralRegistryForm(
            valid_funeral_form_data(burial_date='2020-02-09'), selected_year=2020
        )
        self.assertFalse(form.is_valid())
        self.assertIn('burial_date', form.errors)


class FuneralContentHashTests(SimpleTestCase):
    def test_hash_is_deterministic_and_changes_with_business_content(self):
        record = FuneralDetails(
            death_date=date(2020, 2, 10), first_name='Ivan', last_name='Horvat'
        )
        first_hash = record.calculate_content_hash()
        self.assertEqual(first_hash, record.calculate_content_hash())
        self.assertEqual(len(first_hash), 64)
        record.received_anointing = True
        self.assertNotEqual(first_hash, record.calculate_content_hash())


def valid_marriage_form_data(**overrides):
    data = {}
    for name, field in MarriageRegistryForm.base_fields.items():
        if name in {'entry_number', 'physical_page', 'groom_oib', 'bride_oib', 'notes'}:
            data[name] = ''
        elif name == 'marriage_date':
            data[name] = '2020-06-20'
        elif name.endswith('birth_date'):
            data[name] = '1990-01-10'
        elif name.endswith('baptism_date'):
            data[name] = '1990-03-10'
        else:
            data[name] = 'Podatak'
    data.update(overrides)
    return data


class MarriageRegistryFormTests(SimpleTestCase):
    def test_optional_oibs_notes_and_page_are_accepted(self):
        form = MarriageRegistryForm(valid_marriage_form_data(), selected_year=2020)
        self.assertTrue(form.is_valid(), form.errors)

    def test_oib_format_is_validated(self):
        form = MarriageRegistryForm(
            valid_marriage_form_data(groom_oib='123'), selected_year=2020
        )
        self.assertFalse(form.is_valid())
        self.assertIn('groom_oib', form.errors)

    def test_baptism_cannot_precede_birth(self):
        form = MarriageRegistryForm(
            valid_marriage_form_data(groom_baptism_date='1989-01-01'),
            selected_year=2020,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('groom_baptism_date', form.errors)


class MarriageContentHashTests(SimpleTestCase):
    def test_hash_changes_with_business_content(self):
        record = MarriageDetails(
            marriage_date=date(2020, 6, 20),
            groom_first_name='Ivan', bride_first_name='Ana',
        )
        first_hash = record.calculate_content_hash()
        self.assertEqual(first_hash, record.calculate_content_hash())
        record.notes = 'Dispenza'
        self.assertNotEqual(first_hash, record.calculate_content_hash())
