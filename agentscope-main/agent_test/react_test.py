# -*- coding: utf-8 -*-
"""Retrieve service working with memory specially."""
from typing import Callable, Optional, Any, Sequence
from loguru import logger

from agentscope.service.service_response import ServiceResponse
from agentscope.service.service_status import ServiceExecStatus
from agentscope.models import ModelWrapperBase
from cos_sim import cos_sim
import json

def retrieve_from_list(
    query: Any,
    knowledge: Sequence,  # TODO: rename
    score_func: Callable[[Any, Any], float] = cos_sim,
    top_k: int = 2,
    embedding_model: Optional[ModelWrapperBase] = None,
    preserve_order: bool = True,
) -> ServiceResponse:
    """
    Retrieve data in a list.

    Memory retrieval with user-defined score function. The score function is
    expected to take the `query` and one of the element in 'knowledge' (a
    list). This function retrieves top-k elements in 'knowledge' with
    HIGHEST scores. If the 'query' is a dict but has no embedding,
    we use the embedding model to embed the query.

    Args:
        query (`Any`):
            A message to be retrieved.
        knowledge (`Sequence`):
            Data/knowledge to be retrieved from.
        score_func (`Callable[[Any, Any], float]`):
            User-defined function for comparing two messages.
        top_k (`int`, defaults to `None`):
            Maximum number of messages returned.
        embedding_model (`Optional[ModelWrapperBase]`, defaults to `None`):
            A model to embed the query/message.
        preserve_order (`bool`, defaults to `True`):
            Whether to preserve the original order of the retrieved data.
            Defaults to True.

    Returns:
        `ServiceResponse`: The top-k retrieved messages with HIGHEST scores.
    """
    if isinstance(query, dict):
        if embedding_model is not None and "embedding" not in query:
            query_embed = embedding_model(
                query
            ).embedding[0]
        elif embedding_model is None and "embedding" not in query:
            logger.warning(
                "Since the input query has no embedding, embedding model is "
                "is not provided either.",
            )
    # with open('output_file.json', 'w', encoding='utf-8') as file:
    #     json.dump(query["embedding"].embedding, file)
    # print(len(query["embedding"].embedding))
    # (score, index, object)
    scores = [
        (score_func(query_embed, embedding_model(msg).embedding[0]), i, msg) for i, msg in enumerate(knowledge)
    ]

    # ordered by score, and extract the top-k items with highest scores
    top_k = len(scores) if top_k is None else top_k
    ordered_top_k_scores = sorted(scores, key=lambda x: x[0], reverse=True)[
        :top_k
    ]

    # if keep the original order
    if preserve_order:
        # ordered by index
        content = sorted(ordered_top_k_scores, key=lambda x: x[1])
    else:
        content = ordered_top_k_scores

    # The returned content includes a list of triples of (score, index, object)
    print(content)
    return ServiceResponse(
        status=ServiceExecStatus.SUCCESS,
        content=content,
    )
