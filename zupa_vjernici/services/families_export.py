"""Izvoz popisa obitelji u Excel (.xlsx)."""
from __future__ import annotations

from datetime import date
from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from django.http import HttpResponse

from zupa_vjernici.services.families_page import filter_families

_CONTENT_TYPE = (
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)


def families_xlsx_response(parish_data: dict, request) -> HttpResponse:
    """Vrati xlsx s prikazanim obiteljima i njihovim članovima."""
    streets = {
        street['id']: street
        for street in parish_data.get('streets', [])
    }
    families = filter_families(
        list(parish_data.get('families', [])),
        street_id=request.GET.get('street', ''),
        search_term=(request.GET.get('q') or '').strip(),
        lukno=request.GET.get('lukno', ''),
        lukno_year=date.today().year - 1,
    )
    workbook = _workbook_bytes(
        [
            ('Obitelji', _family_rows(families, streets)),
            ('Članovi', _member_rows(families)),
        ]
    )
    filename = f'obitelji_{date.today().isoformat()}.xlsx'
    response = HttpResponse(workbook, content_type=_CONTENT_TYPE)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _family_rows(families: list[dict], streets: dict) -> list[list[object]]:
    rows: list[list[object]] = [[
        'Prezime',
        'Adresa',
        'Ulica',
        'Članovi',
        'Telefon',
        'E-mail',
        'Zadnji posjet',
        'Status',
    ]]
    for family in families:
        street = streets.get(family.get('streetId') or '') or {}
        rows.append([
            family.get('surname') or '',
            family.get('address') or '',
            street.get('name') or '',
            len(family.get('members') or []),
            family.get('phone') or '',
            family.get('email') or '',
            family.get('lastVisit') or '',
            family.get('status') or 'aktivna',
        ])
    return rows


def _member_rows(families: list[dict]) -> list[list[object]]:
    rows: list[list[object]] = [[
        'Obitelj',
        'Ime i prezime',
        'Odnos',
        'Godina rođenja',
    ]]
    for family in families:
        surname = family.get('surname') or ''
        members = family.get('members') or []
        if not members:
            rows.append([surname, '', '', ''])
            continue
        for family_member in members:
            rows.append([
                surname,
                family_member.get('name') or '',
                family_member.get('relation') or '',
                family_member.get('birthYear') or '',
            ])
    return rows


def _workbook_bytes(sheets: list[tuple[str, list[list[object]]]]) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', _content_types_xml(len(sheets)))
        archive.writestr('_rels/.rels', _root_rels_xml())
        archive.writestr('xl/workbook.xml', _workbook_xml(sheets))
        archive.writestr('xl/_rels/workbook.xml.rels', _workbook_rels_xml(len(sheets)))
        archive.writestr('xl/styles.xml', _styles_xml())
        for index, (_sheet_name, rows) in enumerate(sheets, start=1):
            archive.writestr(
                f'xl/worksheets/sheet{index}.xml',
                _worksheet_xml(rows),
            )
    return buffer.getvalue()


def _content_types_xml(sheet_count: int) -> str:
    sheet_overrides = ''.join(
        (
            '<Override PartName="/xl/worksheets/sheet'
            f'{index}.xml" ContentType="application/vnd.openxmlformats-officedocument'
            '.spreadsheetml.worksheet+xml"/>'
        )
        for index in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        f'{sheet_overrides}'
        '</Types>'
    )


def _root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )


def _workbook_xml(sheets: list[tuple[str, list[list[object]]]]) -> str:
    sheet_entries = []
    for index, (sheet_name, _rows) in enumerate(sheets, start=1):
        safe_name = escape(sheet_name[:31])
        sheet_entries.append(
            f'<sheet name="{safe_name}" sheetId="{index}" r:id="rId{index}"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets>{"".join(sheet_entries)}</sheets>'
        '</workbook>'
    )


def _workbook_rels_xml(sheet_count: int) -> str:
    relationships = ''.join(
        (
            f'<Relationship Id="rId{index}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{index}.xml"/>'
        )
        for index in range(1, sheet_count + 1)
    )
    styles = (
        f'<Relationship Id="rId{sheet_count + 1}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'{relationships}{styles}'
        '</Relationships>'
    )


def _styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border/></borders>'
        '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
        '<cellXfs count="1"><xf/></cellXfs>'
        '</styleSheet>'
    )


def _worksheet_xml(rows: list[list[object]]) -> str:
    sheet_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = ''.join(
            _cell_xml(column_index, row_index, value)
            for column_index, value in enumerate(row, start=1)
        )
        sheet_rows.append(f'<row r="{row_index}">{cells}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        '</worksheet>'
    )


def _cell_xml(column_index: int, row_index: int, value: object) -> str:
    reference = f'{_column_letter(column_index)}{row_index}'
    if isinstance(value, int) and not isinstance(value, bool):
        return f'<c r="{reference}"><v>{value}</v></c>'
    text = escape(str(value or ''), {'"': '&quot;'})
    return f'<c r="{reference}" t="inlineStr"><is><t xml:space="preserve">{text}</t></is></c>'


def _column_letter(column_index: int) -> str:
    remaining = column_index
    letters = []
    while remaining:
        remaining, remainder = divmod(remaining - 1, 26)
        letters.append(chr(65 + remainder))
    return ''.join(reversed(letters))
