"""Evaluation and reproducibility API endpoints."""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from app.core.security import require_role
from app.models.schemas import BenchmarkRunResponse
from app.services.evaluation_benchmark import EvaluationBenchmark, BENCHMARK_DATASET

router = APIRouter(prefix="/evaluation", tags=["AI/ML Evaluation"])


@router.get("/benchmark", response_model=BenchmarkRunResponse)
def run_evaluation_benchmark(
    user: dict = Depends(require_role("viewer"))
):
    """
    Executes the reproducible offline evaluation benchmark suite.
    Measures precision, recall, F1, and numeric detection against labeled ground truth.
    """
    results = EvaluationBenchmark.run_benchmark()
    return BenchmarkRunResponse(**results)


@router.get("/dataset")
def get_benchmark_dataset(
    user: dict = Depends(require_role("viewer"))
) -> List[Dict[str, Any]]:
    """Returns the labeled ground-truth evaluation dataset."""
    return BENCHMARK_DATASET
