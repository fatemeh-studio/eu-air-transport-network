# GitHub & local repo setup
# European Air Transport Network project

Follow these steps once, in order, before opening the Claude Project chat.

---

## Step 1 — Create the GitHub repo

1. Go to https://github.com/new
2. Repository name: `eu-air-transport-network`
3. Description: `Complex systems analysis of European aviation: centrality, community detection, and resilience`
4. Set to **Public** (portfolio must be visible)
5. Check: ✅ Add a README file
6. .gitignore template: **Python**
7. License: **MIT**
8. Click **Create repository**

---

## Step 2 — Clone locally

```bash
cd ~/projects          # or wherever you keep your work
git clone https://github.com/YOUR_USERNAME/eu-air-transport-network.git
cd eu-air-transport-network
```

Open the folder in Cursor:
```bash
cursor .
```

---

## Step 3 — Create the folder structure

```bash
mkdir -p src data notebooks sql/queries figures network_viz docs
touch src/__init__.py src/build_graph.py src/load_db.py src/utils.py
touch sql/schema.sql
touch data/README.md
```

---

## Step 4 — Download the OpenFlights data files

```bash
cd data
curl -O https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat
curl -O https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat
cd ..
```

These files have no header row. The column schemas are:

**airports.dat** (14 columns, comma-separated):
Airport ID, Name, City, Country, IATA, ICAO, Latitude, Longitude,
Altitude, Timezone, DST, Tz, Type, Source

**routes.dat** (9 columns, comma-separated):
Airline, Airline ID, Source airport, Source airport ID,
Destination airport, Destination airport ID, Codeshare, Stops, Equipment

---

## Step 5 — Update .gitignore

Add these lines to the existing Python .gitignore that GitHub created:

```
# Project-specific
network.db
network_viz/*.html
*.ipynb_checkpoints
data/raw/

# Quarto intermediates
/.quarto/
*_files/
```

Note: data/airports.dat and data/routes.dat ARE tracked in git (small, static files).

---

## Step 6 — Set up the conda environment

```bash
conda create -n eu-air-network python=3.11 -y
conda activate eu-air-network
conda install -c conda-forge networkx pandas numpy scipy matplotlib plotly jupyter ipykernel nbstripout quarto python-kaleido scikit-learn -y
pip install python-louvain pyvis powerlaw
python -m ipykernel install --user --name eu-air-network --display-name "EU Air Network"
```

---

## Step 7 — Create requirements.txt

```bash
cat > requirements.txt << 'EOF'
networkx>=3.2
pandas>=2.0
numpy>=1.24
scipy>=1.11
matplotlib>=3.7
plotly>=5.18
jupyter>=1.0
ipykernel>=6.0
python-louvain>=0.16
pyvis>=0.3.2
nbstripout>=0.7
python-kaleido>=1.3.0
powerlaw>=1.5
scikit-learn>=1.3
EOF
```

---

## Step 8 — Install the nbstripout git filter 

conda activate eu-air-network
nbstripout --install --attributes .gitattributes
nbstripout --status

---

## Step 9 — Quarto reports

quarto check
### only after a notebook is complete and committed:
quarto render --execute

---

## Step 10 — First real commit

```bash
git add .
git commit -m "initial project structure with OpenFlights data and conda env"
git push origin main
```

---

## Step 11 — Open the Claude Project and start building

In the Claude Project chat, start with:

> "I've set up the repo and downloaded airports.dat and routes.dat. Let's start
> with notebook 01: loading the data, filtering to Europe, building the NetworkX
> graph, and the first Plotly route map."

Claude will build each file. As you receive code:
1. Save it to the correct path in Cursor
2. Run it (notebook cell or script)
3. If it works: `git add <file> && git commit -m "[nb01] <short description>"`
4. If it errors: paste the error back into chat

---

## Workflow for each Claude response that includes code

```
Claude gives code for src/build_graph.py
  → Save to eu-air-transport-network/src/build_graph.py in Cursor
  → Run: python src/build_graph.py   (or run the notebook cell)
  → Works? → git add src/build_graph.py && git commit -m "[src] add EU airport filter"
  → Error? → paste traceback into Claude chat
```

---

## Do you need to upload the project plan?

No — all project details (notebooks, research questions, techniques, quality
standards) are embedded in PROJECT_INSTRUCTIONS.md, which you paste into
the Claude Project custom instructions field. The Claude Project will have full
context without needing an uploaded file.

However, if you want to upload it anyway as a reference document, export
PROJECT_INSTRUCTIONS.md and add it to the Project's file section. It won't hurt.
