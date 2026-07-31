"""Marketing Campaign Agent."""
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent, AgentResponse


class MarketingAgent(BaseAgent):
    name = "marketing"
    description = "خبير تسويق - حملات إعلانية واستراتيجيات انتشار"
    icon = "📢"
    color = "#FF9800"

    async def process(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        platform = context.get("platform", "linkedin") if context else "linkedin"

        system = (
            "أنت خبير تسويق رقمي وإعلانات بخبرة 15 عاماً. "
            "ابتكر حملات إبداعية وعملية مع نصوص جاهزة للنشر."
        )

        prompt = f"""المنتج/الخدمة: {user_input[:1500]}
المنصة المستهدفة: {platform}

المطلوب:
1. 3 أفكار حملات إعلانية مبتكرة مع شرح كل فكرة
2. نصوص إعلانات جاهزة (عنوان جذاب + وصف مقنع + دعوة للعمل)
3. كلمات مفتاحية مستهدفة (10-15 كلمة)
4. استراتيجية انتشار فيروسي خطوة بخطوة
5. جدول زمني للحملة (أسبوع 1-4)
6. ميزانية مقترحة لكل قناة"""

        content = await self._generate(system, prompt, temp=0.8, max_tokens=3000)

        return AgentResponse(
            content=content,
            agent_name=self.name,
            confidence=0.88,
            metadata={"type": "marketing_campaign", "platform": platform}
        )
