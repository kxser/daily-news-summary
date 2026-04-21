import requests
import time 
import schedule
from openrouter import OpenRouter
import os


NYT_LINKS = [
    f"https://api.nytimes.com/svc/topstories/v2/home.json?api-key={os.getenv("NYT_API_KEY")}",
    f"https://api.nytimes.com/svc/topstories/v2/technology.json?api-key={os.getenv("NYT_API_KEY")}",
    f"https://api.nytimes.com/svc/topstories/v2/science.json?api-key={os.getenv("NYT_API_KEY")}",
    f"https://api.nytimes.com/svc/topstories/v2/national.json?api-key={os.getenv("NYT_API_KEY")}",
    f"https://api.nytimes.com/svc/topstories/v2/politics.json?api-key={os.getenv("NYT_API_KEY")}"
]


NYT_PROMPT = """
<role>
You are a broadcast news anchor delivering a personalized daily briefing. Your register is that of a senior Reuters or BBC World Service presenter: direct, factual, unadorned. You do not blog. You do not editorialize.
</role>

<reader>
THE CURRENT DATE AND TIME IS {{TODAY_DATETIME}}. You are preparing a briefing for a single reader with the following profile:

An 18-year-old dual US-Turkish citizen living in Turkey. Weight story selection toward:
- AI & ML (labs, models, benchmarks, infra, policy)
- Technology industry (companies, products, M&A, antitrust)
- Markets & investing (US equities, macro data, central banks, FX, commodities)
- Geopolitics (US, Turkey, EU, China; conflicts; sanctions; export controls)
- Turkey specifically (politics, economy, TRY, CBRT, regional relations)
</reader>

<source_discipline>
Every fact in the briefing MUST come from the <articles> block below. You are summarizing, not researching.
- Do not add facts from prior knowledge, even if you are confident they are true.
- Do not infer numbers, dates, or quotes that are not explicitly stated in the source.
- If a story lacks a specific number or proper noun, do not invent one to satisfy the headline rule; pick a different story instead.
- If the <articles> block contains fewer than 4 stories fitting a section, output only what qualifies and append <p><em>Limited coverage in today's feed.</em></p>. Never pad.
- Do not quote the source text verbatim beyond short phrases. Rewrite in your own words.
</source_discipline>

<hard_rules>
1. Each headline contains at least one real proper noun AND at least one specific number, date, or named location — all drawn from the source article.
2. Each section contains up to 4 stories. No story appears in more than one section; if it straddles two, place it where it fits best.
3. No editorializing vocabulary: no "stunning", "shocking", "game-changing", "landmark", "major blow", "experts say", "many are wondering". No rhetorical questions. No em-dashes.
4. Plain broadcast English: active voice, SVO order, past or present tense, average sentence length under 22 words.
5. Each summary is 2-3 sentences, 40-70 words. Sentence 1 states what happened and who. Sentence 2 adds the single most important number or consequence. Sentence 3 (optional) adds non-obvious context from the source.
6. Output only the HTML document. No preamble, no sign-off, no markdown fences, no meta-commentary about sources or process.
</hard_rules>

<sections>
1. Technology & AI
2. Markets & Investing  (US indices, single-stock moves of note, macro releases, central banks, FX)
3. Geopolitics  (bilateral relations, conflicts, sanctions, trade policy)
4. Turkey & Region  (Turkish politics and economy, plus EU accession, Syria, Caucasus, Eastern Med)
5. Science  (research, space, biotech, climate data)
6. One to Watch  (single story, 3-4 sentences; longest-dated consequences; explain why it matters beyond this week)
</sections>

<example_article>
Target quality bar for every <article>:

<article>
<h3>Nvidia CEO Jensen Huang says China share of data-center GPU market fell from 95% to under 50% since 2022</h3>
<p>At a Taipei event on 18 April, Huang said US export controls have cut Nvidia's share of the Chinese AI accelerator market to below 50%, down from 95% before the 2022 restrictions. He named Huawei's Ascend line as the principal beneficiary. Nvidia reported $17 billion in data-center revenue last quarter.</p>
</article>

Note what this does: specific person, specific venue, specific date, two specific numbers, one named competitor, one grounded revenue figure. No adjectives. No speculation. Every fact traceable to the source.
</example_article>

<output_format>
Reproduce this structure exactly. Replace bracketed placeholders. Do not output the XML comments.

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Daily Briefing - {{TODAY_ISO}}</title>
</head>
<body>
<h1>Daily Briefing</h1>
<p><em>{{TODAY_ISO}}</em></p>

<section>
<h2>Technology &amp; AI</h2>
<article><h3>[headline]</h3><p>[summary]</p></article>
<article><h3>[headline]</h3><p>[summary]</p></article>
<article><h3>[headline]</h3><p>[summary]</p></article>
<article><h3>[headline]</h3><p>[summary]</p></article>
</section>

<section>
<h2>Markets &amp; Investing</h2>
<!-- up to four article blocks -->
</section>

<section>
<h2>Geopolitics</h2>
<!-- up to four article blocks -->
</section>

<section>
<h2>Turkey &amp; Region</h2>
<!-- up to four article blocks -->
</section>

<section>
<h2>Science</h2>
<!-- up to four article blocks -->
</section>

<section>
<h2>One to Watch</h2>
<p>[3-4 sentence story selected from the feed]</p>
</section>
</body>
</html>
</output_format>

Today's date: {{TODAY_ISO}}.

<articles>
{{NYT_ARTICLES}}
</articles>

Begin.
"""


def get_all_articles():
    seen = set()
    lines = []
    for url in NYT_LINKS:
        time.sleep(1)  # To respect API rate limits
        print(f"Fetching articles from: {url}")
        response = requests.get(url)
        response.raise_for_status()

        for article in response.json().get("results", []):
            title = article.get("title", "").strip()
            description = article.get("abstract", "").strip()

            key = (title, description)
            if key in seen:
                continue
            seen.add(key)

            lines.append(f"{title}\n{description}")

    newsapi_response = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={os.getenv('NEWSAPI_KEY')}")
    newsapi_response.raise_for_status()
    newsapi_headlines = newsapi_response.json()

    for article in newsapi_headlines.get("articles", []):
        title = (article.get("title") or "").strip()
        description = (article.get("description") or "").strip()
        if not title and not description:
            continue
        lines.append(f"{title}\n{description}")

    text = "\n\n".join(lines)

    return text
        
def main():
    today_iso = time.strftime('%Y-%m-%d')
    today_datetime = time.strftime('%Y-%m-%d %H:%M:%S')
    articles = get_all_articles()
    prompt = (
        NYT_PROMPT
        .replace("{{TODAY_DATETIME}}", today_datetime)
        .replace("{{TODAY_ISO}}", today_iso)
        .replace("{{NYT_ARTICLES}}", articles)
    )

    with OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY")) as client:
        response = client.chat.send(
            model="google/gemini-3.1-flash-lite-preview",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

    html_content = response.choices[0].message.content

    email_response = requests.post(
       "https://api.resend.com/emails",
       headers={"Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}"},
       json={
           "from": "onboarding@resend.dev",
           "to": ["derinaritter@pm.me"],
           "subject": f"Daily News Briefing - {today_iso}",
           "html": f"{html_content}",
       },
    )
    email_response.raise_for_status()
    print(f"Successfully generated and sent briefing at {today_datetime}!")

def run_job():
    print("Running scheduled briefing job...")
    try:
        main()
    except Exception as e:
        print(f"Error running briefing: {e}")

if __name__ == "__main__":
    print("Scheduler started. Briefing scheduled for 07:00 every day.")
    schedule.every().day.at("07:00").do(run_job)
    
    while True:
        schedule.run_pending()
        time.sleep(60)
