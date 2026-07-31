"""Content Creator Agent."""
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent, AgentResponse


class ContentAgent(BaseAgent):
    name = "content"
    description = "منشئ محتوى - كتب، دورات، منتجات رقمية"
    icon = "📚"
    color = "#9C27B0"

    async def process(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        content_type = context.get("content_type", "ebook") if context else "ebook"

        system = (
            "أنت خبير إنشاء محتوى رقمي وكاتب محترف. "
            "تنشئ أدلة شاملة ودورات تعليمية ومنتجات رقمية عالية الجودة."
        )

        templates = {
            "ebook": "كتاب إلكتروني شامل مع فصول منظمة",
            "course": "خطة دورة تعليمية مع وحدات وتمارين",
            "guide": "دليل عملي خطوة بخطوة",
            "webinar": "خطة ندوة أونلاين مع محتوى العرض"
        }

        template = templates.get(content_type, templates["ebook"])

        prompt = f"""الفكرة: {user_input[:1500]}
نوع المحتوى: {template}

أنشئ:
1. عنوان جذاب وفرعي
2. ملخص تنفيذي (200 كلمة)
3. هيكل تفصيلي مع الفصول/الوحدات
4. محتوى الفصل الأول كاملاً (1000 كلمة)
5. نصائح للتسويق والبيع
6. خطة إطلاق (30 يوم)"""

        content = await self._generate(system, prompt, temp=0.7, max_tokens=3500)

        return AgentResponse(
            content=content,
            agent_name=self.name,
            confidence=0.90,
            metadata={"type": "content_creation", "content_type": content_type}
        )
