# 🧪 SOFIA – Prototipo API Offerte di Lavoro (in fase di test)

![Stato aggiornamento JSON](https://github.com/ferrigabriele/job-offers-api/actions/workflows/update.yml/badge.svg?branch=main)

🚠 **Attenzione:** Questo repository contiene una **versione sperimentale** utilizzata per la costruzione del **prototipo SOFIA**, l’assistente virtuale per i Centri per l’Impiego del Lazio.

> I dati esposti sono **non ufficiali**, **non esaustivi** e potrebbero contenere **inesattezze**.  
> L'utilizzo è riservato esclusivamente a **scopi di test e sviluppo**.

---

## 🔗 JSON pubblico (non ufficiale)

📄 File JSON completo generato ogni giorno (prototipo):  
**[Clicca qui per visualizzare il file JSON completo](https://ferrigabriele.github.io/job-offers-api/data/data.json)**

📄 File JSON ridotto (ultime 60 offerte con link):  
**[Clicca qui per visualizzare il file JSON ridotto](https://ferrigabriele.github.io/job-offers-api/data/data_min.json)**

---

## 🧠 Cos'è SOFIA?

SOFIA è un **assistente virtuale sperimentale** progettato per supportare le attività dei CPI nella consultazione delle offerte di lavoro.  
Questo prototipo connette GPT con un file JSON aggiornato automaticamente.

---

## 💡 Cosa fa questo prototipo?

- Converte un file Excel ospitato su Google Drive in formato JSON
- Filtra solo le offerte `Standard`
- Esporta due file JSON:
  - uno **completo** con tutte le offerte
  - uno **ridotto** con massimo 60 offerte pubblicate (con link)
- Fornisce link diretti al portale regionale (se presenti)

---

## 🗕 Aggiornamento automatico

🕒 I file JSON vengono aggiornati ogni giorno alle **04:00 italiane (02:00 UTC)** tramite GitHub Actions.

🔴 Se il badge in alto è rosso, significa che l’aggiornamento **non è riuscito**.

---

## 🛠 Tecnologie utilizzate

- Python + Pandas
- GitHub Actions
- Google Drive (Excel condiviso pubblicamente)
- GitHub Pages

---

## ⚠️ AVVISO IMPORTANTE

> Questo progetto **non è destinato alla consultazione pubblica dei cittadini**.  
> I dati sono incompleti, soggetti a errore e usati solo a fini di **prototipazione tecnica interna**.

---

## 📩 Contatti e contributi

Per proporre miglioramenti o collaborazioni tecniche:
- GitHub: [ferrigabriele](https://github.com/ferrigabriele)
- Email disponibile su richiesta privata

---

## 📌 Licenza

© 2025 – Questo prototipo non ha licenza d’uso. Non distribuire dati o codice senza autorizzazione
