# NIL Sponsor Manager — Completed instructor demo

Includes the November 17, 19 and 24 Streamlit coding labs in one app.

## Run in GitHub Codespaces
1. Extract this ZIP. Create a new private GitHub repository.
2. Upload app.py, requirements.txt, README.md and .gitignore (if visible) from the extracted folder and commit.
3. Choose Code > Codespaces > Create codespace on main.
4. Open Terminal > New Terminal. Run:

    python -m pip install -r requirements.txt
    python -m streamlit run app.py --server.address 0.0.0.0

5. Open port 8501 in the browser. Keep the port private.

## Test the completed labs
- Home: expect 5 businesses, 3 agreements, $2,550 total.
- Business Directory: choose Apparel (1 record), then All Industries (5). Search by city. Add B06, edit it, then delete it. Try a duplicate ID. Try deleting B01: the foreign key should prevent deletion.
- NIL Agreements: expect 3 rows sorted by compensation (1200, 850, 500).
- Reports: expect 5 businesses, including 3 with no agreements. Peachtree Sportswear has 2 agreements totaling $1,700; Metro Fitness has 1 totaling $850. Both charts should appear.

The app automatically creates nil_demo.db. No database upload is needed. A small DEMO_SETUP metadata table prevents reseeding after deletions. Agreement entry/editing is not part of these labs; the agreements page is read-only. The ERD conference is a separate classroom activity, not a software feature.

To reset the demo, stop Streamlit with Ctrl+C, delete nil_demo.db (this permanently removes local changes), then rerun the Streamlit command. Stop the Codespace when finished. Commit source changes if desired; do not commit the generated database.
