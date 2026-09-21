# Namjera arhitekture podataka

**Primarni dokument:** `MDs/DB_ARCHITECTURE_PROPOSAL.md`  
**Baze:** `core/models.py`

1. Svaki poslovni model je DIM SCD1 / SCD2 / SCD2A ili FACT FCTA (FCTB samo uz opravdan volumen).
2. **Person** je SCD1. **Household** je SCD2A. **HouseholdMembership** je SCD2.
3. Sakramenti i retci matice su **FCTA**. Knjige su **SCD1**.
4. Financije: jedna blagajna **FCTA**, četiri koda ledgera.
5. Kalendarski događaj i zadatak su dva **FCTA** modela.
6. Javne prijave su **FCTA** ulaz, nikad automatski zaključana matica.
7. Naslijediti `core.models`; SCD pisati kroz `save_new`. SCD2 verziju pokreće usporedba polja, ne hash.
8. Čitati SCD2 samo s otvorenog reda (`Model.current`). Povijest se zatvara, ne briše.
9. Latinska župa i Križevačka eparhija: `canonical_tradition` + jurisdikcija + `LiturgicalTradition`. Nema tablice `ChurchSuiIuris`.
