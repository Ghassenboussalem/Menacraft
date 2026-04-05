"""
Demo script for Instagram Bot Detection Pipeline
Demonstrates all 5 stages of the pipeline
"""

from bot_detection_pipeline import InstagramBotDetectionPipeline
import pandas as pd

def demo_fake_dataset():
    """Demo with fake account detection dataset"""
    print("\n" + "="*70)
    print("DEMO 1: FAKE ACCOUNT DETECTION")
    print("="*70 + "\n")
    
    # Initialize pipeline with rule-based scoring
    pipeline = InstagramBotDetectionPipeline(scoring_method='weighted_rules')
    
    # Run full pipeline
    results = pipeline.run_full_pipeline(
        dataset_path="data",
        dataset_version="fake-v1.0"
    )
    
    # Show sample results
    print("\nSample Results:")
    print(results.head(10))
    
    # Show high-confidence bot accounts
    print("\nTop 10 Most Likely Bots:")
    top_bots = results.nlargest(10, 'bot_score')
    print(top_bots[['bot_score', 'classification', 'ground_truth']])
    
    return pipeline, results

def demo_automated_dataset():
    """Demo with automated account detection dataset"""
    print("\n" + "="*70)
    print("DEMO 2: AUTOMATED ACCOUNT DETECTION")
    print("="*70 + "\n")
    
    # Initialize pipeline with rule-based scoring
    pipeline = InstagramBotDetectionPipeline(scoring_method='weighted_rules')
    
    # Run full pipeline
    results = pipeline.run_full_pipeline(
        dataset_path="data",
        dataset_version="automated-v1.0"
    )
    
    # Show sample results
    print("\nSample Results:")
    print(results.head(10))
    
    return pipeline, results

def demo_ml_classifier():
    """Demo with ML-based classifier"""
    print("\n" + "="*70)
    print("DEMO 3: MACHINE LEARNING CLASSIFIER (Random Forest)")
    print("="*70 + "\n")
    
    # Initialize pipeline with Random Forest
    pipeline = InstagramBotDetectionPipeline(scoring_method='random_forest')
    
    # Run full pipeline
    results = pipeline.run_full_pipeline(
        dataset_path="data",
        dataset_version="fake-v1.0"
    )
    
    return pipeline, results

def demo_gradient_boosting():
    """Demo with Gradient Boosting classifier"""
    print("\n" + "="*70)
    print("DEMO 4: GRADIENT BOOSTING CLASSIFIER")
    print("="*70 + "\n")
    
    # Initialize pipeline with Gradient Boosting
    pipeline = InstagramBotDetectionPipeline(scoring_method='gradient_boosting')
    
    # Run full pipeline
    results = pipeline.run_full_pipeline(
        dataset_path="data",
        dataset_version="automated-v1.0"
    )
    
    return pipeline, results

if __name__ == "__main__":
    # Run demos
    print("\n" + "#"*70)
    print("# INSTAGRAM BOT DETECTION PIPELINE - DEMO")
    print("#"*70)
    
    # Demo 1: Fake dataset with rule-based scoring
    pipeline1, results1 = demo_fake_dataset()
    
    # Demo 2: Automated dataset with rule-based scoring
    pipeline2, results2 = demo_automated_dataset()
    
    # Demo 3: ML classifier (Random Forest)
    try:
        pipeline3, results3 = demo_ml_classifier()
    except Exception as e:
        print(f"\nML Demo failed: {e}")
    
    # Demo 4: Gradient Boosting
    try:
        pipeline4, results4 = demo_gradient_boosting()
    except Exception as e:
        print(f"\nGradient Boosting Demo failed: {e}")
    
    print("\n" + "#"*70)
    print("# ALL DEMOS COMPLETE")
    print("#"*70)
