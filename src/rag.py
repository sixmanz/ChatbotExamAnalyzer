import re

class MultiSubjectRAG:
    """ระบบ RAG สำหรับหลายวิชา - สามารถเก็บหลักสูตรหลายไฟล์"""
    
    def __init__(self):
        self.curricula = {}  # {name: {"text": str, "sections": list}}
        self.active_name = None
        
    def add_curriculum(self, name, text):
        """เพิ่มหลักสูตรใหม่"""
        sections = re.split(r'(?=\n(?:[ก-ฮ]\s*\d+\.\d+|[A-Z]\s*\d+\.\d+))', text)
        sections = [s.strip() for s in sections if len(s.strip()) > 20]
        
        self.curricula[name] = {
            "text": text,
            "sections": sections
        }
        
        # Auto-select if first one
        if not self.active_name:
            self.active_name = name
            
        return len(sections)
        
    def remove_curriculum(self, name):
        """ลบหลักสูตร"""
        if name in self.curricula:
            del self.curricula[name]
            if self.active_name == name:
                self.active_name = list(self.curricula.keys())[0] if self.curricula else None
                
    def set_active(self, name):
        """เลือกหลักสูตรที่ใช้งาน"""
        if name in self.curricula:
            self.active_name = name
            
    def get_names(self):
        """ดึงรายชื่อหลักสูตรทั้งหมด"""
        return list(self.curricula.keys())
    
    @property
    def curriculum_text(self):
        """สำหรับ backward compatibility"""
        if self.active_name and self.active_name in self.curricula:
            return self.curricula[self.active_name]["text"]
        return ""
    
    @property
    def sections(self):
        """สำหรับ backward compatibility"""
        if self.active_name and self.active_name in self.curricula:
            return self.curricula[self.active_name]["sections"]
        return []
        
    def search(self, query, top_k=2):
        """ค้นหาจากหลักสูตรที่ active อยู่"""
        if not self.active_name or self.active_name not in self.curricula:
            return "No curriculum selected."
            
        sections = self.curricula[self.active_name]["sections"]
        if not sections:
            return "Curriculum has no sections."
            
        scores = []
        query_words = set(re.findall(r'\w+', query.lower()))
        
        for section in sections:
            score = sum(1 for word in query_words if word in section.lower())
            scores.append((score, section))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        results = [s[1] for s in scores[:top_k] if s[0] > 0]
        
        if not results:
            return "No relevant curriculum standard found."
            
        return "\n...\n".join(results)

# Singleton Global Instance
rag_engine = MultiSubjectRAG()
