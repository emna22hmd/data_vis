import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import time

# ── Config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="FoodLens",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@600;700&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #f7f5f0;
    color: #1a1a1a;
}
h1, h2, h3 { font-family: 'Lora', serif; }

section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e8e4dd;
}
section[data-testid="stSidebar"] * { color: #1a1a1a !important; }

.hero {
    background: linear-gradient(135deg, #e8f4e8 0%, #f0f7ee 60%, #eaf0f7 100%);
    border: 1px solid #c8dfc8;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
}
.hero h1 { font-size: 2.6rem; font-weight: 700; color: #2d5a27; margin: 0; }
.hero p  { color: #5a7a55; font-size: 1rem; margin-top: 0.4rem; }

.metric-card {
    background: #ffffff;
    border: 1px solid #e8e4dd;
    border-radius: 12px;
    padding: 1.2rem 1rem;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.metric-card .val  { font-family:'Lora',serif; font-size:2.2rem; font-weight:700; color:#3a7d44; }
.metric-card .label{ color:#888; font-size:0.8rem; text-transform:uppercase; letter-spacing:.05em; margin-top:.2rem; }

.section-title {
    font-family: 'Lora', serif;
    font-size: 1.25rem;
    font-weight: 600;
    color: #2d5a27;
    border-left: 3px solid #3a7d44;
    padding-left: .75rem;
    margin: 1.5rem 0 .8rem 0;
}

.recette-card {
    background: #ffffff;
    border: 1px solid #e8e4dd;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: .6rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.recette-card .rank  { font-family:'Lora',serif; font-size:1.5rem; color:#3a7d44; font-weight:700; }
.recette-card .titre { font-size:1rem; font-weight:600; color:#1a1a1a; }
.recette-card .meta  { color:#888; font-size:.8rem; margin-top:.2rem; }

.badge {
    display:inline-block; background:#eef6ef; color:#3a7d44;
    border:1px solid #c8dfc8; border-radius:20px;
    padding:2px 10px; font-size:.75rem; margin-right:4px;
}
.score-pill {
    background:#eef6ef; color:#2d5a27; border-radius:20px;
    padding:4px 14px; font-size:.95rem; font-weight:600;
    border:1px solid #c8dfc8;
}

.stButton > button {
    background:#3a7d44 !important; color:white !important;
    border:none !important; border-radius:8px !important;
    font-weight:500 !important; padding:.45rem 1.4rem !important;
}
.stButton > button:hover { background:#2d5a27 !important; }
</style>
""", unsafe_allow_html=True)

# ── Constantes ────────────────────────────────────────────────
BASE_MEALDB = "https://www.themealdb.com/api/json/v1/1"

TRADUCTION_EN = {
    'sucre':'sugar','farine':'flour','beurre':'butter','oeuf':'egg','oeufs':'egg',
    'lait':'milk','sel':'salt','chocolat':'chocolate','vanille':'vanilla','miel':'honey',
    'noix':'nuts','amande':'almond','noisette':'hazelnut','coco':'coconut','avoine':'oats',
    'sésame':'sesame','caramel':'caramel','citron':'lemon','fraise':'strawberry',
    'framboise':'raspberry','pomme':'apple','banane':'banana','crème':'cream',
    'fromage':'cheese','yaourt':'yoghurt','huile':'oil','levure':'yeast',
    'cannelle':'cinnamon','biscuit':'biscuit','cookie':'cookie','gâteau':'cake',
    'pain':'bread','céréale':'cereal','muesli':'muesli','riz':'rice','pâte':'pastry',
}
MOTS_ANGLAIS_DIRECTS = [
    'chocolate','cookie','biscuit','cake','cream','butter','sugar','flour',
    'milk','oat','honey','almond','coconut','vanilla','caramel','lemon',
    'hazelnut','sesame','rice',
]
NUTRI_COLORS = {'A':'#1a9641','B':'#a6d96a','C':'#f4d03f','D':'#f39c12','E':'#e74c3c','NOT-APPLICABLE':'#bbb'}
NOVA_COLORS  = {1:'#2ecc71',2:'#f1c40f',3:'#e67e22',4:'#e74c3c'}
ACCENT = '#3a7d44'

def plotly_layout(fig, height=360, **kw):
    fig.update_layout(
        paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
        font=dict(color='#1a1a1a', family='Inter'),
        height=height, margin=dict(l=10,r=20,t=30,b=10), **kw
    )
    fig.update_xaxes(gridcolor='#f0ece5', linecolor='#e8e4dd')
    fig.update_yaxes(gridcolor='#f0ece5', linecolor='#e8e4dd')
    return fig

# ── Helpers MealDB ────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def extraire_ingredients_off(df):
    mots, resultats, vus = set(), [], set()
    for nom in df['product_name'].dropna():
        for mot in str(nom).lower().split():
            mot = mot.strip('.,()- ')
            if len(mot) > 3: mots.add(mot)
    for mot in mots:
        for fr, en in TRADUCTION_EN.items():
            if fr in mot or mot in fr:
                if en not in vus:
                    vus.add(en); resultats.append({'nom_off':mot,'ingredient_en':en})
                break
        else:
            for en in MOTS_ANGLAIS_DIRECTS:
                if en in mot and en not in vus:
                    vus.add(en); resultats.append({'nom_off':mot,'ingredient_en':en}); break
    return resultats[:30]

@st.cache_data(show_spinner=False)
def fetch_category_recipes(category='Dessert', max_items=30):
    try:
        r = requests.get(f"{BASE_MEALDB}/filter.php", params={'c':category}, timeout=15)
        minis = r.json().get('meals') or []
        details = []
        for mini in minis[:max_items]:
            d = requests.get(f"{BASE_MEALDB}/lookup.php", params={'i':mini['idMeal']}, timeout=15).json()
            meal = (d.get('meals') or [{}])[0]
            if meal:
                ings = []
                for i in range(1,21):
                    ing=(meal.get(f'strIngredient{i}') or '').strip()
                    mes=(meal.get(f'strMeasure{i}')    or '').strip()
                    if ing: ings.append(f"{mes} {ing}".strip())
                details.append({
                    'id':meal.get('idMeal'),'titre':meal.get('strMeal'),
                    'categorie':meal.get('strCategory'),'cuisine':meal.get('strArea'),
                    'tags':meal.get('strTags') or '','ingredients':', '.join(ings),
                    'image':meal.get('strMealThumb'),
                    'url':meal.get('strSource') or f"https://www.themealdb.com/meal/{meal.get('idMeal')}",
                })
            time.sleep(0.2)
        return pd.DataFrame(details)
    except Exception as e:
        st.error(f"Erreur : {e}"); return pd.DataFrame()

def score_recette(row, mots_produits):
    texte = str(row.get('ingredients','')).lower()
    matches = sum(1 for m in mots_produits if m in texte)
    return round(min(matches,10)/10, 3)

def rechercher_par_ingredients(ingredients_en):
    resultats = {}
    for ingredient in ingredients_en:
        try:
            r = requests.get(f"{BASE_MEALDB}/filter.php", params={'i':ingredient}, timeout=15)
            for m in r.json().get('meals') or []:
                mid = m['idMeal']
                if mid not in resultats:
                    resultats[mid] = {'idMeal':mid,'titre':m['strMeal'],'image':m['strMealThumb'],'matches':0,'ingredients_trouves':[]}
                resultats[mid]['matches'] += 1
                resultats[mid]['ingredients_trouves'].append(ingredient)
        except: pass
        time.sleep(0.3)
    if not resultats: return pd.DataFrame()
    return pd.DataFrame(resultats.values()).sort_values('matches',ascending=False).reset_index(drop=True)

def get_meal_detail(meal_id):
    try:
        r = requests.get(f"{BASE_MEALDB}/lookup.php", params={'i':meal_id}, timeout=15)
        return (r.json().get('meals') or [{}])[0]
    except: return {}

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🥗 FoodLens")
    st.markdown("---")
    uploaded = st.file_uploader("📂 Charger le CSV OpenFoodFacts", type="csv")
    st.markdown("---")
    page = st.radio("Navigation", [
        "📊 Exploration OpenFoodFacts",
        "🏆 Recommandations de recettes",
        "🔍 Recherche par ingrédients",
    ])

# ── Chargement ─────────────────────────────────────────────────
if uploaded:
    df = pd.read_csv(uploaded, encoding='utf-8-sig')
else:
    try:    df = pd.read_csv('openfoodfacts_resultats.csv', encoding='utf-8-sig')
    except: df = None

if df is None:
    st.markdown('<div class="hero"><h1>🥗 FoodLens</h1><p>Chargez votre fichier <code>openfoodfacts_resultats.csv</code> via la barre latérale.</p></div>', unsafe_allow_html=True)
    st.stop()

energy_col = next((c for c in df.columns if 'energy' in c.lower() and '100' in c), None)
sugars_col = next((c for c in df.columns if 'sugar'  in c.lower() and '100' in c), None)
nutri_col  = next((c for c in df.columns if 'nutriscore' in c.lower() and 'grade' in c.lower()), None)
nova_col   = next((c for c in df.columns if 'nova' in c.lower()), None)

# ════════════════════════════════════════════════════════════
# PAGE 1 — Exploration (8 plots)
# ════════════════════════════════════════════════════════════
if page == "📊 Exploration OpenFoodFacts":

    st.markdown('<div class="hero"><h1>🥗 Exploration OpenFoodFacts</h1><p>Analyse complète de vos produits scrapés</p></div>', unsafe_allow_html=True)

    nb_cat    = df['categories'].dropna().str.split(',').explode().str.strip().nunique() if 'categories' in df.columns else 0
    nb_marques= df['brands'].dropna().nunique() if 'brands' in df.columns else 0
    nb_pays   = df['countries'].dropna().nunique() if 'countries' in df.columns else 0

    c1,c2,c3,c4 = st.columns(4)
    for col, val, label in [(c1,len(df),"Produits"),(c2,nb_cat,"Catégories"),(c3,nb_marques,"Marques"),(c4,nb_pays,"Pays")]:
        col.markdown(f'<div class="metric-card"><div class="val">{val}</div><div class="label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # PLOT 1 — Nutri-Score
    st.markdown('<div class="section-title">1 · Distribution des Nutri-Scores</div>', unsafe_allow_html=True)
    if nutri_col:
        nc = df[nutri_col].str.upper().value_counts().reindex(['A','B','C','D','E'],fill_value=0).reset_index()
        nc.columns = ['Grade','Nombre']
        fig1 = go.Figure(go.Bar(
            x=nc['Grade'], y=nc['Nombre'],
            marker_color=[NUTRI_COLORS.get(g,'#ccc') for g in nc['Grade']],
            text=nc['Nombre'], textposition='outside',
        ))
        plotly_layout(fig1, height=320, xaxis_title='Grade Nutri-Score', yaxis_title='Nombre de produits')
        st.plotly_chart(fig1, use_container_width=True)

    # PLOT 2 — Nutri-Score par catégorie
    st.markdown('<div class="section-title">2 · Nutri-Score par catégorie principale</div>', unsafe_allow_html=True)
    if nutri_col and 'categories' in df.columns:
        tmp = df[['categories', nutri_col]].dropna().copy()
        tmp[nutri_col] = tmp[nutri_col].str.upper()
        tmp['main_cat'] = tmp['categories'].apply(lambda x: x.split(',')[0].strip() if isinstance(x,str) else x)
        top_cats = tmp['main_cat'].value_counts().head(6).index
        pivot = tmp[tmp['main_cat'].isin(top_cats)].groupby(['main_cat', nutri_col]).size().reset_index(name='count')
        fig2 = px.bar(pivot, x='main_cat', y='count', color=nutri_col,
                      color_discrete_map=NUTRI_COLORS, barmode='stack',
                      labels={'main_cat':'Catégorie','count':'Produits',nutri_col:'Nutri-Score'})
        plotly_layout(fig2, height=360)
        fig2.update_xaxes(tickangle=-20)
        st.plotly_chart(fig2, use_container_width=True)

    col_a, col_b = st.columns(2)

    # PLOT 3 — Top marques
    with col_a:
        st.markdown('<div class="section-title">3 · Top 10 marques</div>', unsafe_allow_html=True)
        if 'brands' in df.columns:
            tb = df['brands'].dropna().str.split(',').explode().str.strip().value_counts().head(10)
            fig3 = px.bar(x=tb.values, y=tb.index, orientation='h',
                          color=tb.values, color_continuous_scale=['#c8dfc8', ACCENT],
                          labels={'x':'Produits','y':''}, text=tb.values)
            plotly_layout(fig3, height=360, coloraxis_showscale=False)
            fig3.update_traces(textposition='outside')
            st.plotly_chart(fig3, use_container_width=True)

    # PLOT 4 — NOVA
    with col_b:
        st.markdown('<div class="section-title">4 · Groupes NOVA</div>', unsafe_allow_html=True)
        if nova_col:
            try:
                nova = df[nova_col].dropna().astype(int).value_counts().sort_index().reset_index()
                nova.columns = ['Groupe','Nombre']
                nova_labels = {1:'Groupe 1\n(Non transformé)',2:'Groupe 2\n(Peu transformé)',3:'Groupe 3\n(Transformé)',4:'Groupe 4\n(Ultra-transformé)'}
                nova['Label']  = nova['Groupe'].map(nova_labels)
                nova['Couleur']= nova['Groupe'].map(NOVA_COLORS)
                fig4 = go.Figure(go.Bar(
                    x=nova['Label'], y=nova['Nombre'],
                    marker_color=nova['Couleur'],
                    text=nova['Nombre'], textposition='outside',
                ))
                plotly_layout(fig4, height=360, yaxis_title='Nombre de produits')
                st.plotly_chart(fig4, use_container_width=True)
            except: st.info("Colonne NOVA non numérique.")
        else: st.info("Colonne nova_group non trouvée.")

    # PLOT 5 — Top catégories
    st.markdown('<div class="section-title">5 · Top 15 catégories alimentaires</div>', unsafe_allow_html=True)
    if 'categories' in df.columns:
        tc = df['categories'].dropna().str.split(',').explode().str.strip().value_counts().head(15)
        fig5 = px.bar(x=tc.values, y=tc.index, orientation='h',
                      color=tc.values, color_continuous_scale=['#c8dfc8', ACCENT],
                      labels={'x':'Nombre de produits','y':''}, text=tc.values)
        plotly_layout(fig5, height=450, coloraxis_showscale=False)
        fig5.update_traces(textposition='outside')
        st.plotly_chart(fig5, use_container_width=True)

    col_c, col_d = st.columns(2)

    # PLOT 6 — Calories vs Sucres
    with col_c:
        st.markdown('<div class="section-title">6 · Calories vs Sucres (pour 100g)</div>', unsafe_allow_html=True)
        if energy_col and sugars_col:
            sc = df[['product_name', energy_col, sugars_col]].dropna().head(200)
            fig6 = px.scatter(sc, x=sugars_col, y=energy_col, hover_name='product_name',
                              color=sugars_col, color_continuous_scale=['#c8dfc8','#e74c3c'],
                              labels={energy_col:'Calories (kcal/100g)', sugars_col:'Sucres (g/100g)'})
            plotly_layout(fig6, height=360, coloraxis_showscale=False)
            st.plotly_chart(fig6, use_container_width=True)
        else: st.info("Colonnes energy/sugars non trouvées.")

    # PLOT 7 — Sucre moyen par Nutri-Score
    with col_d:
        st.markdown('<div class="section-title">7 · Sucre moyen par Nutri-Score</div>', unsafe_allow_html=True)
        if nutri_col and sugars_col:
            sn = df.groupby(df[nutri_col].str.upper())[sugars_col].mean().reindex(['A','B','C','D','E']).dropna().reset_index()
            sn.columns = ['Grade','Sucre_moyen']
            fig7 = go.Figure(go.Bar(
                x=sn['Grade'], y=sn['Sucre_moyen'].round(1),
                marker_color=[NUTRI_COLORS.get(g,'#ccc') for g in sn['Grade']],
                text=sn['Sucre_moyen'].round(1), textposition='outside',
            ))
            plotly_layout(fig7, height=360, yaxis_title='Sucre moyen (g/100g)', xaxis_title='Nutri-Score')
            st.plotly_chart(fig7, use_container_width=True)
        else: st.info("Colonnes nutriscore/sugars non trouvées.")

    # PLOT 8 — Top produits caloriques
    st.markdown('<div class="section-title">8 · Top 10 produits les plus caloriques</div>', unsafe_allow_html=True)
    if 'product_name' in df.columns and energy_col:
        top_cal = df[['product_name', energy_col]].dropna().sort_values(energy_col, ascending=False).head(10)
        fig8 = px.bar(top_cal, x=energy_col, y='product_name', orientation='h',
                      color=energy_col, color_continuous_scale=['#f7c59f','#e74c3c'],
                      labels={energy_col:'Calories (kcal/100g)','product_name':''},
                      text=top_cal[energy_col].round(0))
        plotly_layout(fig8, height=380, coloraxis_showscale=False)
        fig8.update_yaxes(autorange='reversed')
        fig8.update_traces(textposition='outside')
        st.plotly_chart(fig8, use_container_width=True)
    else: st.info("Colonne energy-kcal_100g non trouvée.")

    st.markdown('<div class="section-title">Données brutes</div>', unsafe_allow_html=True)
    st.dataframe(df.head(50), use_container_width=True, height=280)


# ════════════════════════════════════════════════════════════
# PAGE 2 — Recommandations (cartes, sans graphe)
# ════════════════════════════════════════════════════════════
elif page == "🏆 Recommandations de recettes":

    st.markdown('<div class="hero"><h1>🏆 Recommandations</h1><p>Recettes MealDB scorées selon vos produits OpenFoodFacts</p></div>', unsafe_allow_html=True)

    col_l, col_r = st.columns([1,2])
    with col_l:
        categorie = st.selectbox("Catégorie MealDB", ['Dessert','Starter','Breakfast','Side','Vegan','Pasta','Seafood'])
        max_items = st.slider("Recettes à analyser", 10, 40, 25)
    with col_r:
        st.markdown("<br><br>", unsafe_allow_html=True)
        lancer = st.button("▶ Générer les recommandations")

    if lancer:
        with st.spinner("Chargement des recettes..."):
            df_recettes = fetch_category_recipes(categorie, max_items)

        if df_recettes.empty:
            st.error("Aucune recette chargée.")
        else:
            mots_produits = set()
            for nom in df['product_name'].dropna():
                for mot in str(nom).lower().split():
                    mot = mot.strip('.,()-')
                    if len(mot) > 3: mots_produits.add(mot)

            df_recettes['score'] = df_recettes.apply(lambda r: score_recette(r, mots_produits), axis=1)
            df_top = df_recettes.sort_values('score', ascending=False).head(10).reset_index(drop=True)

            st.markdown(f'<div class="section-title">Top {len(df_top)} recettes — {categorie}</div>', unsafe_allow_html=True)

            for i, row in df_top.iterrows():
                tags   = [t.strip() for t in str(row.get('tags','')).split(',') if t.strip()]
                badges = ''.join(f"<span class='badge'>{t}</span>" for t in tags[:3])
                pct    = int(row['score'] * 100)
                st.markdown(f"""
                <div class='recette-card'>
                  <div style='display:flex;align-items:center;gap:1rem;'>
                    <div class='rank'>#{i+1}</div>
                    <div style='flex:1'>
                      <div class='titre'>{row['titre']}</div>
                      <div class='meta'>📂 {row['categorie']} &nbsp;·&nbsp; 🌍 {row['cuisine']}</div>
                      <div style='margin-top:.4rem'>{badges}</div>
                    </div>
                    <div class='score-pill'>{pct}%</div>
                  </div>
                </div>""", unsafe_allow_html=True)

                with st.expander(f"Détails — {row['titre']}"):
                    ca, cb = st.columns([2,1])
                    with ca:
                        st.markdown("**Ingrédients :**")
                        for ing in row['ingredients'].split(','):
                            if ing.strip(): st.markdown(f"• {ing.strip()}")
                    with cb:
                        if row.get('image'): st.image(row['image'], width=180)
                        st.markdown(f"[🔗 Voir la recette]({row['url']})")


# ════════════════════════════════════════════════════════════
# PAGE 3 — Recherche par ingrédients
# ════════════════════════════════════════════════════════════
elif page == "🔍 Recherche par ingrédients":

    st.markdown('<div class="hero"><h1>🔍 Par ingrédients</h1><p>Sélectionnez depuis vos produits OFF ou ajoutez librement</p></div>', unsafe_allow_html=True)

    ingredients_off = extraire_ingredients_off(df)
    if 'selected_ings' not in st.session_state:
        st.session_state['selected_ings'] = []

    st.markdown('<div class="section-title">Depuis vos produits OpenFoodFacts</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for idx, p in enumerate(ingredients_off):
        en = p['ingredient_en']
        with cols[idx % 4]:
            checked = st.checkbox(f"{p['nom_off']} ({en})", value=en in st.session_state['selected_ings'], key=f"cb_{en}")
            if checked and en not in st.session_state['selected_ings']:
                st.session_state['selected_ings'].append(en)
            elif not checked and en in st.session_state['selected_ings']:
                st.session_state['selected_ings'].remove(en)

    st.markdown('<div class="section-title">Ajouter librement (en anglais)</div>', unsafe_allow_html=True)
    saisie = st.text_input("Ex: egg, flour, vanilla", placeholder="Séparez par des virgules...")
    extras = [m.strip().lower() for m in saisie.split(',') if m.strip()] if saisie else []
    tous   = list(dict.fromkeys(st.session_state['selected_ings'] + extras))

    if tous:
        st.markdown("**Sélectionnés :** " + " ".join(f"<span class='badge'>{i}</span>" for i in tous), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔍 Rechercher"):
        if not tous:
            st.warning("Sélectionnez au moins un ingrédient.")
        else:
            with st.spinner(f"Recherche avec {len(tous)} ingrédient(s)..."):
                df_res = rechercher_par_ingredients(tous)

            if df_res.empty:
                st.warning("Aucune recette trouvée. Essayez en anglais : egg, flour, chocolate...")
            else:
                df_show = df_res.head(8).reset_index(drop=True)
                st.success(f"✅ {len(df_res)} recettes trouvées — Top {len(df_show)} :")

                for i, row in df_show.iterrows():
                    found = ', '.join(row['ingredients_trouves'])
                    pct   = int(row['matches'] / len(tous) * 100)
                    st.markdown(f"""
                    <div class='recette-card'>
                      <div style='display:flex;align-items:center;gap:1rem;'>
                        <div class='rank'>#{i+1}</div>
                        <div style='flex:1'>
                          <div class='titre'>{row['titre']}</div>
                          <div class='meta'>✔ {row['matches']}/{len(tous)} ingrédients :
                            <strong style='color:#3a7d44'>{found}</strong>
                          </div>
                        </div>
                        <div class='score-pill'>{pct}%</div>
                      </div>
                    </div>""", unsafe_allow_html=True)

                    with st.expander(f"Détail — {row['titre']}"):
                        detail = get_meal_detail(row['idMeal'])
                        if detail:
                            d1, d2 = st.columns([1,2])
                            with d1:
                                if detail.get('strMealThumb'): st.image(detail['strMealThumb'], use_column_width=True)
                                st.markdown(f"**Catégorie :** {detail.get('strCategory','-')}")
                                st.markdown(f"**Cuisine :** {detail.get('strArea','-')}")
                                if detail.get('strSource'): st.markdown(f"[🔗 Recette complète]({detail['strSource']})")
                            with d2:
                                st.markdown("**Ingrédients :**")
                                for j in range(1,21):
                                    ing=(detail.get(f'strIngredient{j}') or '').strip()
                                    mes=(detail.get(f'strMeasure{j}')    or '').strip()
                                    if ing: st.markdown(f"• {mes} {ing}".strip())
                                st.markdown("**Instructions :**")
                                inst = (detail.get('strInstructions') or '').strip()
                                st.markdown(inst[:700] + ('...' if len(inst)>700 else ''))
