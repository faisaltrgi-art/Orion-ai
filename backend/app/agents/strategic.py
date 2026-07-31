"""Strategic Advisor Agent."""
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent, AgentResponse


class StrategicAgent(BaseAgent):
    name = "strategic"
    description = "مستشار استراتيجي - تحليل SWOT وخطط نمو"
    icon = "📊"
    color = "#4CAF50"

    async def process(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        market_context = context.get("market_data", "") if context else ""

        system = (
            "أنت مستشار استراتيجي للشركات ومدرب تطوير ذاتي متخصص. "
            "قدم تحليلاً دقيقاً وخطة نمو (30-60-90 يوم) قابلة للتطبيق. "
            "استخدم لغة عربية فصحى واضحة."
        )

        prompt = f"""بناءً على: "{user_input}"
والسياق السوقي: {market_context}

قدم تقريراً شاملاً يشمل:
1. تحليل SWOT شخصي/عملي (نقاط القوة، الضعف، الفرص، التهديدات)
2. فجوات تشغيلية وكيفية سدها
3. خطة نمو مرحلية (30-60-90 يوم) بالأتمتة
4. نصائح تطوير ذاتي مرتبطة بالمجال
5. مؤشرات أداء رئيسية (KPIs) لقياس النجاح"""

        content = await self._generate(system, prompt, model="claude", temp=0.4, max_tokens=3000)

        return AgentResponse(
            content=content,
            agent_name=self.name,
            confidence=0.92,
            metadata={"type": "strategic_analysis", "has_swot": True}
        )
