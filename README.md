# 📦 Job Offers API - Regione Lazio (Sofia)

![Stato aggiornamento JSON](https://github.com/ferrigabriele/job-offers-api/actions/workflows/update.yml/badge.svg)

Questo progetto genera ogni giorno un file JSON aggiornato contenente le offerte di lavoro pubblicate nei Centri per l’Impiego del Lazio.

I dati provengono da un file Excel su Google Drive e vengono:
- filtrati per `TipoPreselezione = "Standard"`
- convertiti in JSON
- pubblicati tramite GitHub Pages

---

## 🔗 JSON pubblico

📄 File aggiornato ogni giorno →  
**[Clicca qui per vedere il JSON](https://ferrigabriele.github.io/job-offers-api/data/data.json)**

---

## 📡 Utilizzo via GPT (Sofia)

L’assistente virtuale GPT "Sofia" è configurato per leggere questo JSON e rispondere a domande come:

- “Quali offerte sono in scadenza oggi?”
- “Ci sono opportunità per OSS a Latina?”
- “Mostrami i link ufficiali per candidarmi”

---

## 🛠 Tecnologie usate

- Google Drive (file Excel pubblico)
- GitHub Actions (workflow automatico)
- Python (`pandas`, `requests`)
- GitHub Pages (hosting gratuito del JSON)

---

## 📆 Frequenza aggiornamento

- ✅ Ogni giorno alle ore 4:00 italiane (02:00 UTC)
- ⚠️ Se il badge sopra è rosso, l’ultimo aggiornamento **non è andato a buon fine**

---

## 🤝 Contribuire

Se vuoi proporre filtri, aggiungere nuovi campi o integrare altri flussi regionali:
1. Forka il progetto
2. Apri una pull request
3. Oppure contattaci direttamente

---

## 📧 Contatti

🔗 [GitHub: ferrigabriele](https://github.com/ferrigabriele)
📩 Email amministrativa o tecnica disponibile su richiesta

