# Meeting Cost Calculator

A Streamlit app that shows the hidden labor cost of repeated meetings while waiting for a lower-cost solution such as an API.

## What it does
- Lets you enter the annual cost of a solution
- Maintains a salary table by role
- Converts salary into a loaded hourly rate
- Lets you log meetings and attendee counts by role
- Calculates total meeting labor cost
- Compares meeting cost to the annual cost of the solution
- Visualizes cumulative cost over time

## Starter structure
```text
meeting-cost-calculator/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── salary_table.csv
│   └── meetings.csv
├── assets/
│   └── piggy_bank_mockup.png
└── utils/
    └── calculations.py
```

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
1. Create a new GitHub repo named `meeting-cost-calculator`
2. Upload these files
3. Connect the repo to Streamlit Community Cloud
4. Set `app.py` as the entry point

## Notes
- This starter version uses CSV files for easy editing
- Salary load defaults are editable in the UI
- The piggy bank image is a placeholder/mockup for the dashboard hero area
- You can later add animation, PDF export, and scenario analysis
