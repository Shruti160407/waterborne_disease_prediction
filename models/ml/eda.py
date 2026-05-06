"""
============================================
Exploratory Data Analysis (EDA)
============================================
Performs comprehensive EDA on the water disease CSV dataset.
Generates distribution plots, correlation heatmaps, and statistics.

Usage:
    python models/ml/eda.py
"""

import os
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
warnings.filterwarnings("ignore")

try:
    import pandas as pd
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend for server
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError:
    os.system("pip install pandas numpy matplotlib seaborn")
    import pandas as pd
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

from config.settings import (
    RAW_DATA_DIR, COLUMN_MAPPING, ML_CONFIG, 
    BASE_DIR, WEIGHTS_DIR
)


def load_and_clean_dataset(csv_path: Path = None) -> pd.DataFrame:
    """
    Load the CSV dataset and standardize column names.
    
    This function handles various column naming conventions
    by mapping them to our standardized names.
    
    Args:
        csv_path: Path to the CSV file (default: from settings)
        
    Returns:
        Cleaned DataFrame with standardized column names
    """
    if csv_path is None:
        csv_path = RAW_DATA_DIR / "east_region_india_water_disease_cleaned.csv"
    
    if not csv_path.exists():
        print(f"❌ Dataset not found: {csv_path}")
        print(f"   Download from: https://drive.google.com/file/d/1j1gpnsXFDpgUDPy9vry6uI4HP0p8sl3T/view")
        print(f"   Save to: {csv_path}")
        sys.exit(1)
    
    print(f"📂 Loading dataset: {csv_path}")
    df = pd.read_csv(csv_path)
    
    print(f"   Original shape: {df.shape}")
    print(f"   Original columns: {list(df.columns)}")
    
    # Standardize column names
    # First, try lowercase matching
    new_columns = {}
    for col in df.columns:
        col_lower = col.strip().lower()
        if col_lower in {k.lower(): v for k, v in COLUMN_MAPPING.items()}:
            # Find the matching key
            for key, value in COLUMN_MAPPING.items():
                if key.lower() == col_lower:
                    new_columns[col] = value
                    break
        elif col.strip() in COLUMN_MAPPING:
            new_columns[col] = COLUMN_MAPPING[col.strip()]
        else:
            # Try partial matching
            for key, value in COLUMN_MAPPING.items():
                if key.lower() in col_lower or col_lower in key.lower():
                    new_columns[col] = value
                    break
            
            # If still not mapped, keep original but clean it
            if col not in new_columns:
                clean_name = col.strip().lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
                new_columns[col] = clean_name
    
    df = df.rename(columns=new_columns)
    print(f"   Mapped columns: {list(df.columns)}")
    
    return df


def print_basic_stats(df: pd.DataFrame):
    """Print basic dataset statistics."""
    print(f"\n{'=' * 60}")
    print("📊 BASIC STATISTICS")
    print(f"{'=' * 60}")
    print(f"\n  Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"\n  Data Types:")
    for col, dtype in df.dtypes.items():
        print(f"    {col}: {dtype}")
    
    print(f"\n  Missing Values:")
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("    ✅ No missing values!")
    else:
        for col, count in missing[missing > 0].items():
            pct = count / len(df) * 100
            print(f"    {col}: {count} ({pct:.1f}%)")
    
    print(f"\n  Descriptive Statistics:")
    print(df.describe().to_string())


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values in the dataset.
    
    Strategy:
    - Numerical columns: fill with median
    - Categorical columns: fill with mode
    """
    missing_before = df.isnull().sum().sum()
    
    if missing_before == 0:
        print("\n  ✅ No missing values to handle")
        return df
    
    print(f"\n  🔧 Handling {missing_before} missing values...")
    
    for col in df.columns:
        if df[col].isnull().sum() > 0:
            if df[col].dtype in ['int64', 'float64']:
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
                print(f"    {col}: filled with median ({median_val:.2f})")
            else:
                mode_val = df[col].mode()[0] if len(df[col].mode()) > 0 else "unknown"
                df[col].fillna(mode_val, inplace=True)
                print(f"    {col}: filled with mode ({mode_val})")
    
    missing_after = df.isnull().sum().sum()
    print(f"  ✅ Missing values: {missing_before} → {missing_after}")
    
    return df


def plot_distributions(df: pd.DataFrame, output_dir: Path):
    """
    Plot distribution of all numerical features.
    
    Creates histograms with KDE for each numerical column.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    n_cols = 3
    n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 4 * n_rows))
    fig.suptitle("Feature Distributions", fontsize=16, fontweight="bold", y=1.02)
    
    axes_flat = axes.flatten() if n_rows > 1 else [axes] if n_cols == 1 else axes
    if hasattr(axes, 'flatten'):
        axes_flat = axes.flatten()
    
    for idx, col in enumerate(numeric_cols):
        ax = axes_flat[idx]
        sns.histplot(df[col], kde=True, ax=ax, color=sns.color_palette("viridis", len(numeric_cols))[idx])
        ax.set_title(col.replace("_", " ").title(), fontsize=10)
        ax.set_xlabel("")
    
    # Hide empty subplots
    for idx in range(len(numeric_cols), len(axes_flat)):
        axes_flat[idx].set_visible(False)
    
    plt.tight_layout()
    save_path = output_dir / "feature_distributions.png"
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Saved: {save_path}")


def plot_correlation_heatmap(df: pd.DataFrame, output_dir: Path):
    """
    Plot correlation heatmap of all numerical features.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    numeric_df = df.select_dtypes(include=[np.number])
    corr = numeric_df.corr()
    
    fig, ax = plt.subplots(figsize=(14, 12))
    
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(
        corr, mask=mask, annot=True, fmt=".2f",
        cmap="RdYlBu_r", center=0,
        square=True, linewidths=0.5,
        cbar_kws={"shrink": 0.8},
        ax=ax,
        vmin=-1, vmax=1
    )
    
    ax.set_title("Feature Correlation Heatmap", fontsize=14, fontweight="bold", pad=20)
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.yticks(fontsize=8)
    
    plt.tight_layout()
    save_path = output_dir / "correlation_heatmap.png"
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Saved: {save_path}")


def plot_target_distributions(df: pd.DataFrame, output_dir: Path):
    """
    Plot distributions of target variables (disease cases).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    target_cols = [col for col in ML_CONFIG["target_variables"] if col in df.columns]
    
    if not target_cols:
        print("  ⚠️  Target columns not found in dataset")
        return
    
    fig, axes = plt.subplots(1, len(target_cols), figsize=(6 * len(target_cols), 5))
    
    if len(target_cols) == 1:
        axes = [axes]
    
    colors = ["#e74c3c", "#f39c12", "#3498db"]
    
    for idx, col in enumerate(target_cols):
        sns.histplot(df[col], kde=True, ax=axes[idx], color=colors[idx % len(colors)])
        axes[idx].set_title(col.replace("_", " ").title(), fontsize=12, fontweight="bold")
        axes[idx].axvline(df[col].mean(), color="black", linestyle="--", label=f"Mean: {df[col].mean():.1f}")
        axes[idx].legend()
    
    plt.suptitle("Target Variable Distributions (Disease Cases)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    
    save_path = output_dir / "target_distributions.png"
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Saved: {save_path}")


def plot_feature_vs_target(df: pd.DataFrame, output_dir: Path):
    """
    Plot scatter plots of features vs target variables.
    Shows relationship between water quality parameters and disease cases.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    feature_cols = [col for col in ML_CONFIG["input_features"] if col in df.columns]
    target_cols = [col for col in ML_CONFIG["target_variables"] if col in df.columns]
    
    if not feature_cols or not target_cols:
        print("  ⚠️  Feature or target columns not found")
        return
    
    for target in target_cols:
        n_cols = 4
        n_rows = (len(feature_cols) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 4 * n_rows))
        axes_flat = axes.flatten()
        
        for idx, feature in enumerate(feature_cols):
            ax = axes_flat[idx]
            ax.scatter(df[feature], df[target], alpha=0.3, s=10, c="#3498db")
            ax.set_xlabel(feature.replace("_", " ").title(), fontsize=8)
            ax.set_ylabel(target.replace("_", " ").title(), fontsize=8)
            ax.set_title(f"{feature.split('_')[0]}", fontsize=9)
        
        for idx in range(len(feature_cols), len(axes_flat)):
            axes_flat[idx].set_visible(False)
        
        plt.suptitle(f"Features vs {target.replace('_', ' ').title()}", 
                    fontsize=14, fontweight="bold")
        plt.tight_layout()
        
        save_path = output_dir / f"features_vs_{target}.png"
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  📊 Saved: {save_path}")


def plot_boxplots(df: pd.DataFrame, output_dir: Path):
    """
    Plot boxplots for outlier detection.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    n_cols = 4
    n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 4 * n_rows))
    axes_flat = axes.flatten()
    
    for idx, col in enumerate(numeric_cols):
        sns.boxplot(y=df[col], ax=axes_flat[idx], color=sns.color_palette("Set2")[idx % 8])
        axes_flat[idx].set_title(col.replace("_", " ").title(), fontsize=9)
    
    for idx in range(len(numeric_cols), len(axes_flat)):
        axes_flat[idx].set_visible(False)
    
    plt.suptitle("Feature Boxplots (Outlier Detection)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    
    save_path = output_dir / "feature_boxplots.png"
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Saved: {save_path}")


def run_full_eda():
    """
    Execute the complete EDA pipeline.
    
    Generates all plots and statistics for the water disease dataset.
    """
    print("=" * 60)
    print("📊 EXPLORATORY DATA ANALYSIS")
    print("   Water Disease Dataset - East Region India")
    print("=" * 60)
    
    # Output directory for plots
    eda_output = BASE_DIR / "outputs" / "eda"
    eda_output.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load and clean data
    print("\n📥 Step 1: Loading Dataset...")
    df = load_and_clean_dataset()
    
    # Step 2: Basic statistics
    print_basic_stats(df)
    
    # Step 3: Handle missing values
    print(f"\n{'─' * 60}")
    print("🔧 Step 3: Handling Missing Values")
    df = handle_missing_values(df)
    
    # Step 4: Generate plots
    print(f"\n{'─' * 60}")
    print("📊 Step 4: Generating Visualizations")
    
    plot_distributions(df, eda_output)
    plot_correlation_heatmap(df, eda_output)
    plot_target_distributions(df, eda_output)
    plot_feature_vs_target(df, eda_output)
    plot_boxplots(df, eda_output)
    
    # Step 5: Save cleaned dataset
    cleaned_path = RAW_DATA_DIR / "dataset_cleaned.csv"
    df.to_csv(cleaned_path, index=False)
    print(f"\n  💾 Cleaned dataset saved: {cleaned_path}")
    
    print(f"\n{'=' * 60}")
    print(f"✅ EDA COMPLETE!")
    print(f"   All plots saved to: {eda_output}")
    print(f"{'=' * 60}")
    
    return df


if __name__ == "__main__":
    run_full_eda()
