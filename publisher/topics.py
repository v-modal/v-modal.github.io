"""The catalogue of blog topics and the rotation that picks one per run.

Each topic carries a stable slug (used in the file name and to detect repeats), a
title, tags, a one-line summary for the index, the search prompt sent to the AI
content source, and a self-contained fallback body used when no AI answer is
available. The fallback bodies are written in the same markdown-ish form the AI
sources return (## headings, paragraphs, and - bullet lists) so a single renderer
handles both.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Topic:
    slug: str
    title: str
    tags: List[str]
    summary: str
    prompt: str
    intro: str
    sections: List[tuple] = field(default_factory=list)

    def fallback_body(self) -> str:
        parts = [self.intro.strip()]
        for heading, body in self.sections:
            parts.append(f"## {heading}\n\n{body.strip()}")
        return "\n\n".join(p for p in parts if p).strip()


TOPICS: List[Topic] = [
    Topic(
        slug="multimodal-embeddings",
        title="Joint Embedding Spaces for Multimodal Search",
        tags=["AI", "Search"],
        summary="How shared vector spaces let a single query reach across text, images, and audio.",
        prompt="How do joint embedding spaces power multimodal search across text, images, and audio? Cover contrastive training and nearest-neighbour retrieval.",
        intro=(
            "Multimodal search rests on a simple idea: project every modality into one "
            "shared vector space where similar things land close together, regardless of "
            "whether they started as text, an image, or a sound. Once everything is a "
            "vector, retrieval becomes a nearest-neighbour lookup."
        ),
        sections=[
            ("Why a shared space",
             "A shared space lets a text query match an image, or an image match a sound, "
             "without any hand-built mapping between them. The model learns the alignment "
             "from data, so a photo of a red bicycle and the phrase \"red bicycle\" end up "
             "as neighbours."),
            ("How the alignment is learned",
             "Contrastive training does the work. The model is shown matched and mismatched "
             "pairs and learns to pull matches together while pushing mismatches apart:\n\n"
             "- Supervision comes from naturally occurring pairs, such as images and their captions.\n"
             "- No manual labelling is needed, so the approach scales to hundreds of millions of pairs.\n"
             "- The same recipe extends to audio, depth, and other modalities."),
            ("Turning embeddings into search",
             "At query time the system encodes the query with the same model and looks up "
             "the closest vectors in an index. The quality of the embedding decides the "
             "ceiling on relevance; the index decides how fast you reach it."),
        ],
    ),
    Topic(
        slug="video-retrieval",
        title="Searching Video by Content, Not Tags",
        tags=["AI", "Video"],
        summary="Moving past manual tags to retrieve the exact moment inside a long video.",
        prompt="How does content-based video retrieval work, so a natural-language query can find a specific moment inside a long video?",
        intro=(
            "Tag-based video search only finds what someone remembered to label. "
            "Content-based retrieval indexes what is actually happening on screen, so a "
            "query like \"the moment the belt began to slip\" can land on the right few "
            "seconds of footage."
        ),
        sections=[
            ("Frames are not enough",
             "A single frame rarely captures an action. Useful video retrieval reasons over "
             "short spans of time, so it can tell a hand reaching for a cup from a hand "
             "setting one down."),
            ("The pipeline",
             "A practical system breaks the problem into stages:\n\n"
             "- Sample frames and short clips at a sensible rate rather than every frame.\n"
             "- Encode each clip into an embedding that captures motion and context.\n"
             "- Index the embeddings so a text or image query retrieves the nearest clips.\n"
             "- Re-rank the top candidates with a heavier model for precision."),
            ("Where it pays off",
             "Security review, industrial monitoring, and media archives all share the same "
             "need: find a specific event in hours of footage without watching all of it."),
        ],
    ),
    Topic(
        slug="audio-event-search",
        title="Audio Event Search Beyond Speech-to-Text",
        tags=["AI", "Audio"],
        summary="Indexing environmental sound so a failing part or an alarm becomes searchable.",
        prompt="How can audio search index environmental and non-speech sounds so specific acoustic events become searchable?",
        intro=(
            "Speech-to-text answers only \"what was said\". A large share of useful signal in "
            "audio is non-verbal: a bearing starting to grind, glass breaking, a specific "
            "alarm. Audio event search indexes those sounds directly."
        ),
        sections=[
            ("From waveform to embedding",
             "Raw audio is turned into a time-frequency representation and encoded into "
             "embeddings that capture the character of a sound rather than its transcript. "
             "Similar sounds sit close together in the resulting space."),
            ("What it unlocks",
             "Treating sound as a first-class, searchable type enables:\n\n"
             "- Retrieval of unique acoustic signatures, such as a failing mechanical part.\n"
             "- Alignment of sound events with a visual timeline for review.\n"
             "- Alerting when a known event recurs in a live stream."),
            ("Keeping it robust",
             "Real environments are noisy. Training on varied backgrounds and normalising "
             "levels keeps retrieval stable when the same event is recorded in different places."),
        ],
    ),
    Topic(
        slug="edge-inference",
        title="Running Multimodal Models at the Edge",
        tags=["AI", "Edge"],
        summary="Why physical systems push inference onto the device, and how models are shrunk to fit.",
        prompt="Why is on-device (edge) inference necessary for physical AI, and what techniques shrink multimodal models to run locally?",
        intro=(
            "For a drone dodging an obstacle or a robot on a factory floor, a round trip to "
            "the cloud is too slow. Edge inference runs the model on the device itself, "
            "trading raw model size for latency, reliability, and privacy."
        ),
        sections=[
            ("The case for local compute",
             "Processing high-fidelity video and audio centrally is costly and slow, and it "
             "fails the moment the network does. Local compute gives:\n\n"
             "- Low latency for real-time decisions.\n"
             "- Offline reliability, independent of connectivity.\n"
             "- Privacy, by keeping sensitive feeds on the device."),
            ("Making models fit",
             "Quantisation, pruning, and distillation reduce a model's size and cost while "
             "keeping most of its accuracy. Hardware-aware tuning then matches the model to "
             "the accelerator it will actually run on."),
            ("A tiered approach",
             "Many systems keep a small, fast model on the edge for the common case and "
             "escalate rare, hard inputs to a larger model when a connection is available."),
        ],
    ),
    Topic(
        slug="streaming-sensor-fusion",
        title="Aligning Streaming Sensor Data in Real Time",
        tags=["AI", "Streaming"],
        summary="How real-time pipelines align feeds that arrive at different rates before analysing them.",
        prompt="How do real-time pipelines align and fuse streaming sensor data that arrives at different rates for physical AI systems?",
        intro=(
            "A physical system is fed by a continuous tide of raw data: camera frames, "
            "microphones, and sensors, all arriving at different rates. Making sense of it "
            "starts with alignment, not analysis."
        ),
        sections=[
            ("Different feeds, different clocks",
             "Cameras, audio arrays, and sensors sample at their own speeds. Before anything "
             "can be fused, timestamped feeds have to be aligned onto a common timeline."),
            ("Building the pipeline",
             "Robust streaming pipelines lean on a few ideas:\n\n"
             "- Event-driven processing instead of fixed batches.\n"
             "- Buffering and windowing to align feeds that drift apart.\n"
             "- Smart filtering, so only high-value data triggers heavy computation or storage."),
            ("Why filtering matters",
             "Storing and processing everything is wasteful. Deciding early what deserves "
             "attention keeps a real-time system affordable and fast."),
        ],
    ),
    Topic(
        slug="ann-indexing",
        title="Approximate Nearest-Neighbour Indexing at Scale",
        tags=["AI", "Search"],
        summary="The indexing structures that keep vector search fast across billions of items.",
        prompt="How does approximate nearest-neighbour indexing keep vector search fast and accurate across billions of embeddings?",
        intro=(
            "Once every document is an embedding, search is a nearest-neighbour problem. "
            "Exact search over billions of vectors is too slow, so production systems use "
            "approximate indexes that trade a little recall for a large speed-up."
        ),
        sections=[
            ("The exact-search wall",
             "Comparing a query against every vector does not scale. Approximate nearest-"
             "neighbour (ANN) indexes narrow the search to a promising subset first."),
            ("Common index families",
             "A few structures dominate practical systems:\n\n"
             "- Graph indexes such as HNSW, which walk a navigable small-world graph.\n"
             "- Inverted-file and clustering methods that route a query to a few partitions.\n"
             "- Product quantisation, which compresses vectors so more fit in memory."),
            ("Tuning the trade-off",
             "Every ANN index exposes a recall-versus-speed knob. The right setting depends "
             "on how costly a missed result is against how fast the query must return."),
        ],
    ),
    Topic(
        slug="physical-ai-perception",
        title="Perception Loops for Physical AI",
        tags=["AI", "Physical AI"],
        summary="How embedded systems perceive, retrieve context, and act inside a tight loop.",
        prompt="How does a physical AI system close the loop from multi-sensory perception to retrieving context and acting in real time?",
        intro=(
            "Physical AI is intelligence embedded in machines that act in the real world. "
            "Its defining trait is a tight loop: perceive through many senses, retrieve "
            "relevant context, decide, and act, over and over."
        ),
        sections=[
            ("Perception is multi-sensory",
             "A machine on a factory floor does not rely on video alone. It combines visual "
             "frames, temperature, and vibration to understand a situation more completely "
             "than any single sense allows."),
            ("Retrieval closes the loop",
             "Multimodal search acts as the machine's memory. Faced with a new situation it "
             "can:\n\n"
             "- Match the current state against past events.\n"
             "- Retrieve the context needed to interpret what it is seeing.\n"
             "- Feed that context into a split-second decision."),
            ("Latency sets the limit",
             "Because the loop drives physical action, its speed is a hard constraint. This "
             "is what pushes so much of the perception stack onto the edge."),
        ],
    ),
    Topic(
        slug="cross-modal-retrieval",
        title="Cross-Modal Retrieval: Text-to-Image and Back",
        tags=["AI", "Search"],
        summary="Describing a concept in one modality and retrieving matches in another.",
        prompt="How does cross-modal retrieval let a text query return images, or an image query return text, using shared embeddings?",
        intro=(
            "Cross-modal retrieval is multimodal search at its most direct: describe "
            "something in text and get back matching images, or hand the system an image and "
            "get back the text that describes it. One shared space makes both directions the "
            "same operation."
        ),
        sections=[
            ("One space, two directions",
             "Because text and images live in the same embedding space, \"text finds image\" "
             "and \"image finds text\" are the same nearest-neighbour query run from either "
             "starting point."),
            ("Where the gap shows",
             "The alignment is imperfect, and a few problems recur:\n\n"
             "- A modality gap can leave text and image vectors in slightly different regions.\n"
             "- Fine-grained details, such as counting or exact spatial relations, are hard.\n"
             "- Web-trained models inherit the biases of their data.\n"
             "Re-ranking the top candidates with a joint model recovers much of the lost precision."),
            ("Putting it to work",
             "Visual product search, caption retrieval, and content moderation all reduce to "
             "the same cross-modal lookup once the embeddings are in place."),
        ],
    ),
]


def all_topics() -> List[Topic]:
    return list(TOPICS)


def get_topic(slug: str):
    for t in TOPICS:
        if t.slug == slug:
            return t
    return None


def select_topic(used_slugs, rotation_index: int) -> Topic:
    """Pick the next topic to publish.

    Prefer the first topic whose slug has not been published yet (keeps variety);
    once every topic has appeared, rotate deterministically by `rotation_index` so the
    cycle repeats in order rather than sticking on one topic."""
    used = set(used_slugs or [])
    for t in TOPICS:
        if t.slug not in used:
            return t
    return TOPICS[rotation_index % len(TOPICS)]
