"""Competitor Analysis Agent."""
from typing import Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from app.agents.base import BaseAgent, AgentResponse


class CompetitorAgent(BaseAgent):
    name = "competitor"
    description = "محلل منافسين - تحليل المواقع والبيانات الحية"
    icon = "🔍"
    color = "#2196F3"

    async def _fetch_live_data(self, query: str, max_results: int = 5) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f"{query} ثغرات عيوب تحليل", max_results=max_results))
                return "\n".join([f"{r['title']}: {r['body']}" for r in results])
        except Exception:
            return "لا توجد بيانات حية متاحة."

    async def _analyze_website(self, url: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                text = soup.get_text(separator=" ", strip=True)[:2000]
                return await self._generate(
                    "حلل موقع المنافس من ناحية UX، SEO، الأتمتة، وسير العمل. قدم نقاط قوة وضعف.",
                    text, temp=0.3, max_tokens=1500
                )
        except Exception as e:
            return f"تعذر تحليل الموقع: {str(e)}"

    async def process(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        is_url = user_input.startswith("http")

        if is_url:
            website_analysis = await self._analyze_website(user_input)
            live_data = ""
        else:
            website_analysis = ""
            live_data = await self._fetch_live_data(user_input)

        system = (
            "أنت محلل منافسين استراتيجي. قم بتحليل شامل للمنافسين "
            "مع استخراج نقاط القوة والضعف والفرص."
        )

        prompt = f"""المنافس: {user_input}

{'تحليل الموقع:\n' + website_analysis if website_analysis else ''}
{'البيانات الحية:\n' + live_data if live_data else ''}

قدم تحليلاً يشمل:
1. نظرة عامة على المنافس
2. نقاط القوة (ما يفعله بشكل جيد)
3. نقاط الضعف (ثغرات يمكن استغلالها)
4. الفرص المتاحة في السوق
5. التهديدات المحتملة
6. توصيات عملية للتفوق عليه"""

        content = await self._generate(system, prompt, model="claude", temp=0.4, max_tokens=3000)

        return AgentResponse(
            content=content,
            agent_name=self.name,
            confidence=0.85,
            metadata={"type": "competitor_analysis", "has_website": is_url}
        )
