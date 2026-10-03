import torch
from sentence_transformers import SentenceTransformer, CrossEncoder, util


# ============================================================
# CONFIG
# ============================================================

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CROSS_ENCODER_MODEL = "models/antikopas-cross-encoder"

MINILM_THRESHOLD = 0.50
CROSS_THRESHOLD = 0.05


# ============================================================
# LOAD MODEL
# ============================================================

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)

cross_encoder = CrossEncoder(
    CROSS_ENCODER_MODEL,
    num_labels=1,
    max_length=512
)


# ============================================================
# HYBRID SIMILARITY
# ============================================================

def calculate_hybrid_similarity(
    document_text,
    source_text
):
    """
    Membandingkan satu chunk dokumen
    dengan satu chunk sumber.
    """

    # --------------------------------------------------------
    # STEP 1: MiniLM
    # --------------------------------------------------------

    document_embedding = embedding_model.encode(
        document_text,
        convert_to_tensor=True
    )

    source_embedding = embedding_model.encode(
        source_text,
        convert_to_tensor=True
    )

    minilm_score = util.cos_sim(
        document_embedding,
        source_embedding
    ).item()


    # --------------------------------------------------------
    # STEP 2: Filter kandidat
    # --------------------------------------------------------

    if minilm_score < MINILM_THRESHOLD:

        return {
            "minilm_score": minilm_score,
            "cross_score": None,
            "matched": False
        }


    # --------------------------------------------------------
    # STEP 3: Cross Encoder
    # --------------------------------------------------------

    cross_score = float(
        cross_encoder.predict(
            [
                (
                    document_text,
                    source_text
                )
            ]
        )[0]
    )


    # --------------------------------------------------------
    # STEP 4: Decision
    # --------------------------------------------------------

    matched = cross_score >= CROSS_THRESHOLD


    return {
        "minilm_score": minilm_score,
        "cross_score": cross_score,
        "matched": matched
    }