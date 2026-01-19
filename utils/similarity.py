"""Text similarity calculation utilities.

使用 TF-IDF + 余弦相似度算法计算文本相似度。
支持中文文本。
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def preprocess_text(text: str) -> str:
    """预处理文本：去除标点、统一空格"""
    # 去除标点符号（保留中英文和数字）
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
    # 统一空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def calculate_similarity(text1: str, text2: str) -> float:
    """计算两个文本的相似度（0-1）。
    
    使用 TF-IDF + 余弦相似度算法。
    如果 sklearn 不可用，使用简单的词汇重叠率。
    
    Args:
        text1: 第一个文本
        text2: 第二个文本
    
    Returns:
        相似度分数（0-1），1表示完全相同
    """
    if not text1 or not text2:
        return 0.0
    
    # 预处理
    text1_clean = preprocess_text(text1)
    text2_clean = preprocess_text(text2)
    
    if not text1_clean or not text2_clean:
        return 0.0
    
    if SKLEARN_AVAILABLE:
        try:
            # 使用 TF-IDF + 余弦相似度
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([text1_clean, text2_clean])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception:
            # 如果失败，降级到简单算法
            pass
    
    # 降级方案：简单的词汇重叠率
    words1 = set(text1_clean.split())
    words2 = set(text2_clean.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    if union == 0:
        return 0.0
    
    return intersection / union


def find_similar_pairs(
    texts: List[Tuple[str, str, dict]],  # List of (id, text, metadata)
    threshold: float = 0.8
) -> List[Tuple[dict, dict, float]]:
    """找出相似的文本对。
    
    Args:
        texts: 文本列表，每个元素为 (id, text, metadata)
        threshold: 相似度阈值（0-1）
    
    Returns:
        相似文本对列表，每个元素为 (entry1, entry2, similarity)
    """
    similar_pairs = []
    
    # 合并 title 和 content 作为比较文本
    processed_texts = []
    for entry_id, text, metadata in texts:
        title = metadata.get("title", "")
        content = metadata.get("content", "")
        full_text = f"{title} {content}"
        processed_texts.append((entry_id, full_text, metadata))
    
    # 两两比较
    for i in range(len(processed_texts)):
        for j in range(i + 1, len(processed_texts)):
            id1, text1, meta1 = processed_texts[i]
            id2, text2, meta2 = processed_texts[j]
            
            similarity = calculate_similarity(text1, text2)
            
            if similarity >= threshold:
                similar_pairs.append((meta1, meta2, similarity))
    
    # 按相似度降序排序
    similar_pairs.sort(key=lambda x: x[2], reverse=True)
    
    return similar_pairs
