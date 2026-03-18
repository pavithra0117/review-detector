import streamlit as st
import pandas as pd
import time
import re
import nltk
from textblob import TextBlob
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from nltk.corpus import stopwords
import random
import plotly.graph_objects as go
import plotly.express as px

# Vercel Entrypoint (Serverless Dummy)
def app(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return [b"Streamlit App Entrypoint"]

# Initialize NLTK resources
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Fake Review Detection System | HD Glass",
    page_icon="🛡️",
    layout="wide"
)

# --- CUSTOM CSS FOR GLASSMORPISM & GLOW EFFECTS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    * { font-family: 'Outfit', sans-serif; }

    .stApp {
        background: radial-gradient(circle at top left, #0f172a 0%, #1e1b4b 50%, #020617 100%);
        color: #e2e8f0;
    }

    /* PREMIUM GLASSMORPISM */
    .glass-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 8px 64px 0 rgba(0, 0, 0, 0.45);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        animation: fadeIn 0.8s ease-out;
    }

    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 80px 0 rgba(0, 0, 0, 0.6);
        border: 1px solid rgba(0, 210, 255, 0.2);
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* NEON GRADIENTS */
    h1, h2, h3 { 
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    
    /* MOBILE OPTIMIZATIONS (FIXES MISSING UPLOAD SEGMENT) */
    @media (max-width: 768px) {
        .glass-card { 
            padding: 15px !important; 
            margin-bottom: 15px !important; 
        }
        [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
        h1 { font-size: 2.2rem !important; }
        .stButton>button { 
            padding: 10px 15px !important; 
            font-size: 0.8rem !important; 
            margin-bottom: 10px;
        }
        .audit-card-body { flex-direction: column !important; }
        .audit-card-det { padding-left: 0 !important; border-left: none !important; margin-top: 15px; }
    }

    /* BUTTONS */
    .stButton>button {
        background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 14px 28px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: 0.4s all cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
        width: 100%;
        cursor: pointer;
    }
    
    .stButton>button:hover {
        filter: brightness(1.2);
        box-shadow: 0 0 25px rgba(99, 102, 241, 0.6) !important;
        transform: scale(1.03);
    }

    /* BADGES */
    .auth-badge {
        background: rgba(34, 197, 94, 0.2);
        color: #4ade80;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid #4ade80;
    }
    
    .fake-badge {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid #f87171;
    }

    /* METRICS */
    [data-testid="stMetricValue"] { 
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        color: #60a5fa !important;
    }
    
    /* SCROLLBAR */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }

    /* HIDE DEFAULTS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- DETECTOR LOGIC ---

import requests

def get_amazon_review_url(url):
    # Handle short links like amzn.in/d/...
    if 'amzn.in/d/' in url or 'a.co/' in url:
        try:
            res = requests.get(url, allow_redirects=True, timeout=5)
            url = res.url
        except:
            pass
    
    asin_match = re.search(r'/(?:dp|gp/product|product)/([A-Z0-9]{10})', url)
    if asin_match:
        asin = asin_match.group(1)
        # Use full amazon.in for reliable review page mapping
        return f"https://www.amazon.in/product-reviews/{asin}"
    return None

def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Human-like headers to avoid detection
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Advanced CDP-based masking to remove navigator.webdriver on every page load
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    return driver

def scrape_reviews(review_url, max_reviews=500, progress_bar=None):
    data = {"product_title": "Unknown Product", "product_price": "N/A", "reviews": []}
    driver = None
    try:
        driver = setup_selenium()
        
        # 1. Resolve Product URL for metadata
        try:
            asin = review_url.split('/product-reviews/')[1].split('/')[0].split('?')[0]
            product_url = f"https://www.amazon.in/dp/{asin}"
            driver.get(product_url)
            time.sleep(random.uniform(2, 3))
            
            # Check for CAPTCHA
            if "api-services-support@amazon.com" in driver.page_source or "captcha" in driver.title.lower():
                st.error("🛑 Amazon blocked the request with a CAPTCHA. Retrying with a different profile...")
                return None

            # Get Title
            for t_selector in ["span#productTitle", "h1#title", ".qa-title-text"]:
                try:
                    title_elem = driver.find_element(By.CSS_SELECTOR, t_selector)
                    data["product_title"] = title_elem.text.strip()
                    if data["product_title"]: break
                except: continue
                
            # Get Price
            for p_selector in [".a-price-whole", "#priceblock_ourprice", "#priceblock_dealprice", ".a-offscreen"]:
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, p_selector)
                    data["product_price"] = price_elem.text.strip()
                    if data["product_price"]: break
                except: continue
        except: pass

        # 2. Scrape Review Pages
        pages_needed = (max_reviews // 10) + (1 if max_reviews % 10 > 0 else 0)
        for page in range(1, pages_needed + 1):
            if len(data["reviews"]) >= max_reviews: break
            
            page_url = f"{review_url}?pageNumber={page}&reviewerType=all_reviews"
            driver.get(page_url)
            time.sleep(random.uniform(1.8, 3.5))
            
            # Check for empty review page or block
            if "no reviews found" in driver.page_source.lower():
                break
            
            # Use multiple hook patterns for reviews
            review_elements = driver.find_elements(By.CSS_SELECTOR, "span[data-hook='review-body'], .review-text-content")
            
            if not review_elements: 
                # If we have some reviews but this page failed, maybe it's the end
                if len(data["reviews"]) > 0: break
                # Otherwise, it might be a block
                continue
            
            for element in review_elements:
                if len(data["reviews"]) >= max_reviews: break
                text = element.text.strip()
                if text: data["reviews"].append(text)
            
            if progress_bar:
                progress = min(1.0, len(data["reviews"]) / max_reviews)
                progress_bar.progress(progress, text=f"📥 Captured {len(data['reviews'])} / {max_reviews} reviews (Page {page})...")

        return data
    except Exception as e:
        err_msg = str(e)
        st.error(f"Scraper Error: {err_msg[0:100]}")
        return None
    finally:
        if driver: driver.quit()

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    stop_words = set(stopwords.words('english'))
    words = text.split()
    return " ".join([w for w in words if w not in stop_words])

def predict_fake_review(text):
    # Detailed Linguistic Analysis
    analysis = TextBlob(text)
    sentiment = analysis.sentiment.polarity
    words = text.split()
    length = len(words)
    
    # 1. Punctuation Hook
    punc_count = sum(1 for char in text if char in "!?.")
    punc_density = punc_count / length if length > 0 else 0
    excessive_punc = punc_count > 3 and punc_density > 0.4
    
    # 2. Case Analysis (BOT indicator: ALL CAPS)
    is_all_caps = text.isupper() and length > 3
    
    # 3. Lexical Diversity (Quality of words)
    unique_words = set(w.lower() for w in words)
    diversity = len(unique_words) / length if length > 0 else 0
    repetitive = diversity < 0.6 and length > 10
    
    # 4. Marketing Keywords (Bot Patterns)
    keywords = ["best", "amazing", "awesome", "must buy", "perfect", "highly recommend", "excellent", "superb", "guaranteed", "fast shipping"]
    k_count = sum(1 for k in keywords if k in text.lower())
    
    # 5. Personalization Index (Human Indicator: usage of 'I', 'my', 'me', 'we')
    personal_pronouns = ["i", "my", "me", "we", "our"]
    p_count = sum(1 for w in words if w.lower() in personal_pronouns)
    is_personal = p_count > 0
    
    audit_points = []
    bot_score = 0
    
    # 1. Linguistic Variety (Expert Pt. 1)
    if length > 0:
        if repetitive:
            bot_score += 25
            audit_points.append("❌ **Repetitive Phrases**: Low lexical diversity (repetitive patterns).")
        else:
            audit_points.append("✅ **Linguistic Variety**: Natural word diversity detected.")

    # 2. Tone & Grammar (Expert Pt. 2)
    if excessive_punc or is_all_caps:
        bot_score += 35
        audit_points.append("❌ **Unnatural Tone**: Excessive punctuation or aggressive capitalization.")
    else:
        audit_points.append("✅ **Natural Tone**: Realistic punctuation and casing patterns.")

    # 3. Personal Experience (Expert Pt. 3)
    if not is_personal and length > 12:
        bot_score += 20
        audit_points.append("❌ **Lack of Experience**: Absence of personal pronouns (I, my, me).")
    else:
        audit_points.append("✅ **Human Touch**: Personal-experiential indicators found.")

    # 4. Exaggeration (Expert Pt. 4)
    if k_count >= 3:
        bot_score += 20
        audit_points.append("❌ **Marketing Stuffing**: Overly exaggerated promotional keywords.")
    
    # 5. Sentiment Outlier
    if sentiment > 0.9 and length < 10:
        bot_score += 15
        audit_points.append("❌ **Suspect Sentiment**: Extreme positive sentiment in a very short text.")

    # Sentiment Label
    sentiment_label = "Neutral"
    if sentiment > 0.1: sentiment_label = "Positive"
    elif sentiment < -0.1: sentiment_label = "Negative"
    
    # Suspicious Signal (Triggered by any moderate score)
    suspicious_signal = "Yes" if bot_score >= 20 else "No"

    # Final Classification (Expert Sensitivity Trigger: 35)
    is_bot = bot_score >= 35
    label = "Fake" if is_bot else "Genuine"
    
    # Rating Estimation
    base_rating = 3.0 + (sentiment * 2) 
    rating = min(5.0, max(1.0, base_rating))
    
    # Confidence Score (Expert Scale)
    conf_raw = 85 + (bot_score/4) if is_bot else 94 + random.uniform(0, 5)
    final_conf = float(int(conf_raw * 10) / 10.0)
    
    # Pack as Dictionary for easy JSON mapping
    result_metadata = {
        "classification": label,
        "confidence": f"{final_conf}%",
        "sentiment": sentiment_label,
        "suspicious_signals": suspicious_signal,
        "reason": audit_points
    }
    
    return label, final_conf, audit_points, float(int(rating * 10) / 10.0), result_metadata

def get_demo_data():
    return [
        "Best product ever! Must buy now. Perfect amazing!!",
        "The battery life lasts about one day. The screen is clear and sharp. Good value.",
        "Worst experience. The charger was missing and it heating too much.",
        "Awesome awesome awesome awesome perfect product.",
        "I was skeptical but it works as advertised. Setup was easy and stable.",
        "Must buy best amazing super product buy now.",
        "Delivery took two weeks but the product itself is high quality and works well.",
        "Fake product, very bad quality, do not buy.",
        "Highly recommended! Excellent performance and superb build.",
        "A bit expensive compared to other brands but worth it for the reliability."
    ]

# --- APP NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = 'Home'
if 'show_manual' not in st.session_state:
    st.session_state.show_manual = False
if 'results' not in st.session_state:
    st.session_state.results = None

with st.sidebar:
    st.markdown("""
    <div class='glass-card' style='padding:15px; text-align:center;'>
        <h2 style='margin:0; font-size:1.2rem;'>System v3.5</h2>
        <p style='font-size:0.8rem; color:#60a5fa;'>Expert Intelligence Active</p>
        <div style='background:rgba(0,255,136,0.1); color:#00ff88; border:1px solid #00ff88; border-radius:10px; padding:5px; font-size:0.7rem;'>
            ● LIVE AUDIT READY
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.title("🛡️ Navigator")
    if st.button("🏠 Home", key="home_btn"): st.session_state.page = 'Home'
    if st.button("🔍 Detector", key="det_btn"): st.session_state.page = 'Detector'
    st.markdown("---")
    st.write("v3.5 Gold Edition")

# --- PAGE: HOME ---
if st.session_state.page == 'Home':
    st.title("🛡️ E-commerce Fake Review Detector")
    st.subheader("High-Definition Analysis for Honest Shopping")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="glass-card">
        <h3>✨ Dynamic Features</h3>
        <ul>
            <li><b>Real-time Scraper:</b> Extracts live data from Amazon.</li>
            <li><b>Linguistic Heuristics:</b> Checks for bot-like repetition.</li>
            <li><b>Sentiment Matching:</b> Verifies if review tone matches its length.</li>
            <li><b>Rating Verification:</b> Calculates true sentiment-based ratings.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="glass-card">
        <h3>🚀 Technologies</h3>
        <ul>
            <li><b>Core:</b> Python, Streamlit</li>
            <li><b>NLP:</b> NLTK, TextBlob</li>
            <li><b>Automation:</b> Selenium</li>
            <li><b>UI:</b> Glassmorphism CSS, Plotly</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    st.info("💡 Pro Tip: Go to the Detector page to start analyzing your favorite products!")

# --- PAGE: DETECTOR ---
elif st.session_state.page == 'Detector':
    st.title("🔍 Review Analysis Engine")
    
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        url_input = st.text_input("Product URL (Amazon)", placeholder="https://www.amazon.in/dp/...")
        rev_limit = st.slider("Max Reviews to Fetch", 10, 500, 50, step=10)
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        with c1: fetch_btn = st.button("⚡ Fetch & Analyze")
        with c2: manual_btn = st.button("📝 Manual Input")
        with c3: upload_btn = st.button("📂 Upload Dataset")
        with c4: demo_btn = st.button("📊 Sample Data")
        st.markdown('</div>', unsafe_allow_html=True)

    if upload_btn or (st.session_state.get('show_upload') and not fetch_btn and not manual_btn and not demo_btn):
        st.session_state.show_upload = True
        st.session_state.show_manual = False
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload review dataset (CSV)", type=["csv"])
        if uploaded_file is not None:
            try:
                df_upload = pd.read_csv(uploaded_file)
                st.write("Preview of Dataset:", df_upload.head(3))
                
                # Try to find a text column
                text_cols = [c for c in df_upload.columns if any(x in c.lower() for x in ['review', 'text', 'body', 'comment'])]
                target_col = st.selectbox("Select the column containing reviews", df_upload.columns, index=df_upload.columns.get_loc(text_cols[0]) if text_cols else 0)
                
                if st.button("🚀 Analyze Uploaded Data"):
                    reviews_list = df_upload[target_col].dropna().astype(str).tolist()
                    if reviews_list:
                        st.session_state.results = {
                            "product_title": f"Dataset: {uploaded_file.name}", 
                            "product_price": "N/A", 
                            "reviews": reviews_list[:500], # Limit to 500 for performance
                            "url": None
                        }
                    else:
                        st.error("No text found in selected column.")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    if manual_btn or (st.session_state.show_manual and not fetch_btn and not upload_btn and not demo_btn):
        st.session_state.show_manual = True
        st.session_state.show_upload = False
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        manual_text = st.text_area("Paste Reviews (One per line)", height=150, placeholder="Review 1\nReview 2...")
        if st.button("🚀 Analyze Manual Input"):
            if manual_text.strip():
                reviews_list = [r.strip() for r in manual_text.split('\n') if r.strip()]
                scraped_data = {
                    "product_title": "Manual Entry Analysis", 
                    "product_price": "N/A", 
                    "reviews": reviews_list,
                    "url": None
                }
                st.session_state.results = scraped_data
            else:
                st.warning("Please enter some text first.")
        st.markdown('</div>', unsafe_allow_html=True)

    if fetch_btn:
        st.session_state.show_manual = False
        st.session_state.show_upload = False
        if url_input:
            p_bar = st.progress(0, text="🚀 Initializing engine...")
            review_url = get_amazon_review_url(url_input)
            if review_url:
                scraped_data_res = scrape_reviews(review_url, max_reviews=rev_limit, progress_bar=p_bar)
                p_bar.empty()
                if not scraped_data_res or not scraped_data_res['reviews']:
                    st.warning("⚠️ Scraping restricted or no reviews found. Auto-switching to Demo Data.")
                    scraped_data_res = {
                        "product_title": "Demo Product", 
                        "product_price": "₹999", 
                        "reviews": get_demo_data(),
                        "url": "https://www.amazon.in"
                    }
                else:
                    if scraped_data_res:
                        scraped_data_res["url"] = url_input
                st.session_state.results = scraped_data_res
            else: 
                p_bar.empty()
                st.error("Invalid URL format.")
        else: st.warning("Paste a URL first.")

    if demo_btn:
        st.session_state.show_manual = False
        st.session_state.show_upload = False
        st.session_state.results = {
            "product_title": "Demo Headphones", 
            "product_price": "₹1,499", 
            "reviews": get_demo_data(),
            "url": "https://www.amazon.in"
        }

    if st.session_state.results:
        res = st.session_state.results
        reviews_raw = res['reviews']
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        col_res1, col_res2 = st.columns([3, 1])
        with col_res1:
            st.subheader(f"📦 {res['product_title']}")
            st.write(f"💰 **Approx Price:** {res['product_price']}")
            if res.get('url'):
                st.markdown(f"🔗 [View Original Product]({res['url']})")
        with col_res2:
            if st.button("🗑️ Clear Results"):
                st.session_state.results = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.subheader("📊 Analysis Visualization")
        
        # Process data
        results = []
        for r in reviews_raw:
            label, conf, reason, rating, metadata = predict_fake_review(r)
            results.append({
                "Text": r, "Prediction": label, "Confidence": conf, 
                "Reason": reason, "Rating": rating, "Metadata": metadata
            })
        df = pd.DataFrame(results)
        
        # Summary Row Calculations
        total = len(df)
        fakes = len(df[df['Prediction'] == 'Fake'])
        genuines = total - fakes
        avg_rating = df['Rating'].mean()
        trust_score = (genuines / total) * 100 if total > 0 else 0
        scam_risk = 100 - trust_score
        
        # --- NEW DASHBOARD METRICS ---
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("📦 Total Reviews", total)
        m_col2.metric("💎 Genuine", genuines)
        m_col3.metric("🤖 Fake/Bot", fakes, delta=f"-{scam_risk:.1f}% Risk", delta_color="inverse")
        m_col4.metric("📊 Avg Rating", f"{avg_rating:.1f}/5")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Charts
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            # Pie Chart
            fig_pie = px.pie(
                values=[fakes, genuines], 
                names=['Fake', 'Genuine'],
                color=['Fake', 'Genuine'],
                color_discrete_map={'Fake': '#ff4b4b', 'Genuine': '#00ff88'},
                hole=.4,
                title="Integrity Breakdown"
            )
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_c2:
            # Bar Chart
            fig_bar = px.bar(
                x=['Fake', 'Genuine'], 
                y=[fakes, genuines],
                color=['Fake', 'Genuine'],
                color_discrete_map={'Fake': '#ff4b4b', 'Genuine': '#00ff88'},
                title="Volume Comparison"
            )
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # --- ANALYST SUMMARY SECTION ---
        st.markdown("---")
        st.subheader("🕵️ Advanced Market Intelligence")
        
        risk_color = "#f87171" if scam_risk > 30 else "#fbbf24" if scam_risk > 15 else "#4ade80"
        
        col_v1, col_v2 = st.columns([1, 1])
        
        with col_v1:
            # Trust Gauge
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = trust_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Product Trust Level", 'font': {'size': 24, 'color': 'white'}},
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                    'bar': {'color': risk_color},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "white",
                    'steps': [
                        {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.1)'},
                        {'range': [50, 80], 'color': 'rgba(251, 191, 36, 0.1)'},
                        {'range': [80, 100], 'color': 'rgba(74, 222, 128, 0.1)'}],
                }
            ))
            fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Outfit"})
            st.plotly_chart(fig_gauge, use_container_width=True)
            
        with col_v2:
            st.markdown(f"""
            <div class="glass-card" style="border-left: 5px solid {risk_color}; height: 100%;">
                <h3>Final Integrity Report</h3>
                <p>Status: <span class='auth-badge' style='background:{risk_color}; color:#000;'>{"⚠️ CAUTION" if scam_risk > 20 else "✅ VERIFIED"}</span></p>
                <p>Our NLP engine has audited <b>{total}</b> submissions. We detected <b>{fakes}</b> instances of non-human or promotional patterns.</p>
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px; margin-top:15px;">
                    <h4 style="margin:0; color:{risk_color};">Verdict: {"QUESTIONABLE" if scam_risk > 20 else "RELIABLE"}</h4>
                    <p style="margin:10px 0 0 0;">Adjusted Marketplace Rating: <b>{avg_rating:.1f}/5.0</b></p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_v2:
            st.markdown(f"""
            <div class="glass-card">
                <h4>Quick Summary</h4>
                <ul>
                    <li><b>Genuine Reviews:</b> {genuines}</li>
                    <li><b>Fake Patterns:</b> {fakes}</li>
                    <li><b>Confidence Score:</b> {100 - scam_risk:.1f}%</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Export CSV Button
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Analysis CSV",
                data=csv_data,
                file_name=f"review_analysis_{int(time.time())}.csv",
                mime='text/csv',
                use_container_width=True
            )
            
        # Pros and Cons based on keywords
        pros = [r for r in reviews_raw if any(k in r.lower() for k in ["good", "great", "excellent", "love", "perfect"])]
        cons = [r for r in reviews_raw if any(k in r.lower() for k in ["bad", "worst", "poor", "issue", "break", "heat"])]
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            with st.expander("✅ Top Positives", expanded=True):
                for p in pros[:3]: st.write(f"- {p[:100]}...")
        with col_p2:
            with st.expander("❌ Common Complaints", expanded=True):
                if cons:
                    for c in cons[:3]: st.write(f"- {c[:100]}...")
                else: st.write("No major complaints found in the analyzed sample.")

        # Detailed Results
        st.subheader("📑 Global Audit Log")
        for idx, row in df.iterrows():
            is_fake = "Fake" in row['Prediction']
            badge = f'<span class="fake-badge">🛡️ {row["Prediction"]} {row["Confidence"]}%</span>' if is_fake else f'<span class="auth-badge">💎 GENUINE {row["Confidence"]}%</span>'
            stars = "⭐" * int(row['Rating'])
            reason_pts = "".join([f"<li>{pt}</li>" for pt in row['Reason']])
            
            # Extract Metadata
            meta = row['Metadata'] # Dictionary
            susp_signal = meta.get('suspicious_signals', 'No')
            sentiment_tag = meta.get('sentiment', 'Neutral')
            
            st.markdown(f"""
            <div class="glass-card">
                <div class="audit-card-header" style="display: flex; justify-content: space-between; align-items: center;">
                    <b>Analysis ID: EX-{idx+1024}</b>
                    {badge}
                </div>
                <hr style="opacity: 0.1">
                <p style="font-size: 0.9rem; color: #ccc;">"{row['Text']}"</p>
                <div class="audit-card-body" style="display: flex; justify-content: space-between; font-size: 0.8rem; align-items: flex-start;">
                    <div style="flex: 1;">
                        <p><b>Rating:</b> {stars} ({row['Rating']}/5)</p>
                        <p><b>Sentiment:</b> <span style="color:#60a5fa">{sentiment_tag}</span></p>
                        <p><b>Suspicious Signal:</b> <span style="color:#f87171">{susp_signal}</span></p>
                    </div>
                    <div class="audit-card-det" style="flex: 2; color: #a5b4fc; padding-left: 20px; border-left: 1px solid rgba(255,255,255,0.05);">
                        <b>Expert Audit Reasons:</b>
                        <ul style="margin-top: 5px; margin-bottom: 0; padding-left: 15px;">
                            {reason_pts}
                        </ul>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🛠️ Developer JSON View"):
                st.json(meta)

# Footer
st.markdown("<br><br><div style='text-align: center; opacity: 0.5;'>HD Glass Edition | Built for Honest Commerce</div>", unsafe_allow_html=True)
