"""Social Media Agent."""
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent, AgentResponse


class SocialMediaAgent(BaseAgent):
    name = "social"
    description = "مسوق محتوى - منشورات فيروسية وهاشتاغات"
    icon = "📱"
    color = "#E91E63"

    async def process(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        platforms = context.get("platforms", ["linkedin", "twitter"]) if context else ["linkedin", "twitter"]

        system = (
            "أنت مسوق محتوى سوشيال ميديا محترف. "
            "تنشئ منشورات فيروسية مع هاشتاغات واستراتيجيات انتشار."
        )

        prompt = f"""الموضوع/المنتج: {user_input[:1000]}
المنصات: {', '.join(platforms)}

أنشئ:
1. منشور LinkedIn احترافي (مع هاشتاغات)
2. تغريدة Twitter/X (مع Thread اختياري)
3. منشور Instagram (تعليق جذاب)
4. نص TikTok/Reels (سيناريو قصير)
5. هاشتاغات استراتيجية (20-30 هاشتاغ)
6. أفضل أوقات النشر لكل منصة
7. استراتيجية تفاعل (ردود، مشاركة، تعاون)"""

        content = await self._generate(system, prompt, temp=0.9, max_tokens=2500)

        return AgentResponse(
            content=content,
            agent_name=self.name,
            confidence=0.87,
            metadata={"type": "social_media", "platforms": platforms}
        )
