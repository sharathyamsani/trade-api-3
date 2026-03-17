"""
AI analysis layer.
Uses Google Gemini to generate a structured markdown trade-opportunities report.
Falls back to a template-based report when no API key is configured.
"""
import time
import logging

import httpx

from config import settings
from data_collector import collect_market_data, format_results_for_prompt
from models import AnalysisMetadata

logger = logging.getLogger(__name__)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)

REPORT_PROMPT = """You are an expert trade and economic analyst specializing in Indian markets.

Using the market research data below, generate a comprehensive, structured trade opportunities 
report for the **{sector}** sector in India.

## Market Research Data
{research_data}

## Instructions
Generate a detailed markdown report with the following sections:

1. **Executive Summary** – 3-4 sentence overview of trade opportunities
2. **Current Market Overview** – Market size, growth rate, key players, recent performance
3. **Export Opportunities** – Top export destinations, high-demand products/sub-sectors, competitive advantages
4. **Import Dynamics** – Key imports, import substitution opportunities, dependency areas
5. **Government Policies & Incentives** – PLI schemes, FDI rules, trade agreements, subsidies relevant to this sector
6. **Key Trends & Drivers** – Technology adoption, demand shifts, global supply chain changes
7. **Challenges & Risks** – Regulatory hurdles, competition, infrastructure gaps, geopolitical risks
8. **Investment Opportunities** – FDI hotspots, joint venture potential, emerging sub-segments
9. **Key Trade Partners** – Top countries for trade, bilateral trade data, emerging markets
10. **Recommendations** – 5 actionable insights for businesses and investors

Format rules:
- Use proper markdown headings (## for sections, ### for sub-sections)
- Use bullet points for lists
- Add a data table where relevant (e.g., top export markets with estimated values)
- Include a "Last Updated" line at the bottom: `*Report generated: {timestamp}*`
- Be specific with numbers and percentages where available from the research
- Total length: 800-1200 words
"""


class TradeAnalyzer:
    async def analyze(self, sector: str) -> tuple[str, AnalysisMetadata]:
        """
        Collect data → build prompt → call Gemini → return (markdown_report, metadata).
        """
        results, sources = await collect_market_data(sector)
        research_data = format_results_for_prompt(results) if results else "(No live data retrieved – using general knowledge)"

        timestamp = time.strftime("%B %d, %Y %H:%M UTC", time.gmtime())
        prompt = REPORT_PROMPT.format(
            sector=sector.title(),
            research_data=research_data,
            timestamp=timestamp,
        )

        if settings.GEMINI_API_KEY:
            report = await self._call_gemini(prompt)
            model_used = "gemini-1.5-flash"
        else:
            logger.warning("GEMINI_API_KEY not set – using fallback template report.")
            report = self._fallback_report(sector, timestamp)
            model_used = "fallback-template"

        metadata = AnalysisMetadata(
            generated_at=time.time(),
            sources_used=sources,
            analysis_model=model_used,
            sector_normalized=sector,
        )
        return report, metadata

    async def _call_gemini(self, prompt: str) -> str:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            },
        }
        params = {"key": settings.GEMINI_API_KEY}

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(GEMINI_URL, json=payload, params=params)

        if resp.status_code != 200:
            logger.error("Gemini API error %s: %s", resp.status_code, resp.text[:300])
            raise RuntimeError(f"Gemini API returned {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected Gemini response shape: {exc}") from exc

    @staticmethod
    def _fallback_report(sector: str, timestamp: str) -> str:
        return f"""# Trade Opportunities Report: {sector.title()} Sector – India

> ⚠️ **Demo Mode** – Set `GEMINI_API_KEY` in `.env` to enable AI-powered analysis.

## Executive Summary
India's {sector} sector presents significant trade opportunities driven by strong domestic demand,
government-backed incentive programmes, and expanding global integration.

## Current Market Overview
- India is among the world's fastest-growing economies, providing a large domestic market.
- The {sector} sector contributes meaningfully to GDP and employment.
- Key players include both public-sector enterprises and private conglomerates.

## Export Opportunities
- High-value product exports to the USA, EU, and emerging ASEAN markets.
- Quality certification and compliance are key enablers.
- Competitive labour costs and skilled workforce support export competitiveness.

## Import Dynamics
- Machinery, raw materials, and technology components are primary imports.
- Import substitution initiatives under Atmanirbhar Bharat aim to reduce dependency.

## Government Policies & Incentives
- **PLI Scheme**: Production-Linked Incentive for eligible segments.
- **FDI**: Up to 100% FDI allowed in most sub-sectors via automatic route.
- **Trade Agreements**: CEPA and bilateral agreements with key partners.

## Key Trends & Drivers
- Digital transformation and Industry 4.0 adoption.
- Sustainability and ESG compliance becoming table stakes.
- Rising middle class boosting domestic consumption.

## Challenges & Risks
- Infrastructure bottlenecks (logistics, power).
- Regulatory complexity and compliance costs.
- Competition from China and Southeast Asian manufacturers.

## Investment Opportunities
- Greenfield manufacturing in designated industrial corridors.
- Joint ventures for technology transfer.
- Export-oriented units (EOUs) and SEZs.

## Key Trade Partners
| Partner | Trade Relationship |
|---------|-------------------|
| USA     | Major export destination |
| China   | Key import source |
| UAE     | Re-export hub |
| EU      | Premium market |

## Recommendations
1. Leverage PLI incentives to scale domestic manufacturing.
2. Pursue quality certifications (ISO, GMP) to access premium export markets.
3. Explore FTA opportunities under newly signed trade agreements.
4. Invest in R&D to move up the value chain.
5. Build strategic partnerships with global players for technology access.

---
*Report generated: {timestamp}*
"""
