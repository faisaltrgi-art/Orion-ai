"""Quality Auditor Agent."""
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent, AgentResponse


class AuditorAgent(BaseAgent):
    name = "auditor"
    description = "مدقق جودة - تحسين المحتوى وتصحيح الأخطاء"
    icon = "✅"
    color = "#607D8B"

    async def process(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        system = (
            "أنت مدقق جودة محتوى محترف ومدقق لغوي. "
            "قم بتحسين النص دون تغيير المعنى، صحح الأخطاء، أضف أمثلة، وحسّن التدفق."
        )

        prompt = f"""راجع وحسّن التقرير/النص التالي:

{user_input[:4000]}

المطلوب:
1. تصحيح الأخطاء الإملائية والنحوية
2. تحسين الوضوح والتدفق
3. إضافة أمثلة توضيحية حيثما يناسب
4. تقوية العناوين والمقدمات
5. تنسيق Markdown مناسب
6. ملخص التحسينات المُجراة"""

        content = await self._generate(system, prompt, temp=0.2, max_tokens=3000)

        return AgentResponse(
            content=content,
            agent_name=self.name,
            confidence=0.95,
            metadata={"type": "quality_audit", "improvements_made": True}
        )
