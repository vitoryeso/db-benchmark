#!/usr/bin/env python3
"""
Compare Results - Analyze and visualize benchmark results
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from tabulate import tabulate
import click
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style for plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class ResultsAnalyzer:
    """Analyze and visualize benchmark results"""
    
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.databases = ['postgres', 'mongodb', 'couchdb', 'cassandra', 'scylladb']
        self.colors = {
            'postgres': '#336791',
            'mongodb': '#47A248',
            'couchdb': '#E42528',
            'cassandra': '#1287B6',
            'scylladb': '#FF6B6B'
        }
    
    def load_results(self, test_type: str) -> Dict[str, pd.DataFrame]:
        """Load results for all databases for a specific test type"""
        results = {}
        
        for db in self.databases:
            pattern = f"{db}_{test_type}_*.csv"
            files = list(self.results_dir.glob(pattern))
            
            if files:
                # Get the most recent file
                latest_file = max(files, key=os.path.getctime)
                logger.info(f"Loading {db} {test_type} results from {latest_file}")
                results[db] = pd.read_csv(latest_file)
            else:
                logger.warning(f"No {test_type} results found for {db}")
        
        return results
    
    def plot_scalability_comparison(self, save_path: str = "results/scalability_comparison.png"):
        """Create line plot comparing scalability across databases"""
        results = self.load_results("scalability")
        
        if not results:
            logger.error("No scalability results found")
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot 1: Mean latency vs records
        for db, df in results.items():
            ax1.plot(df['records_in_db'], df['query_mean_latency'] * 1000,  # Convert to ms
                    label=db.upper(), color=self.colors[db], linewidth=2, marker='o')
        
        ax1.set_xlabel('Number of Records in Database')
        ax1.set_ylabel('Mean Query Latency (ms)')
        ax1.set_title('Query Performance vs Database Size', fontsize=16, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: P95 latency vs records
        for db, df in results.items():
            ax2.plot(df['records_in_db'], df['query_p95_latency'] * 1000,  # Convert to ms
                    label=db.upper(), color=self.colors[db], linewidth=2, marker='s')
        
        ax2.set_xlabel('Number of Records in Database')
        ax2.set_ylabel('P95 Query Latency (ms)')
        ax2.set_title('P95 Query Latency vs Database Size', fontsize=16, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Scalability comparison saved to {save_path}")
        plt.close()
    
    def plot_load_test_distribution(self, save_path: str = "results/load_test_distribution.png"):
        """Create box plots showing latency distribution for load tests"""
        summary_results = self.load_results("load_test_summary")
        detailed_results = self.load_results("load_test_detailed")
        
        if not summary_results:
            logger.error("No load test results found")
            return
        
        # Prepare data for box plot
        plot_data = []
        for db, df in detailed_results.items():
            for _, row in df.iterrows():
                plot_data.append({
                    'Database': db.upper(),
                    'Latency': row['mean_latency'] * 1000  # Convert to ms
                })
        
        plot_df = pd.DataFrame(plot_data)
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Box plot
        box_plot = sns.boxplot(data=plot_df, x='Database', y='Latency', ax=ax1,
                              palette=[self.colors[db.lower()] for db in plot_df['Database'].unique()])
        ax1.set_ylabel('Query Latency (ms)')
        ax1.set_title('Query Latency Distribution Under Load', fontsize=16, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Add median values on top of boxes
        medians = plot_df.groupby('Database')['Latency'].median()
        for i, (db, median) in enumerate(medians.items()):
            ax1.text(i, median, f'{median:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Bar plot for percentiles
        percentile_data = []
        for db, df in summary_results.items():
            if not df.empty:
                row = df.iloc[0]
                percentile_data.append({
                    'Database': db.upper(),
                    'Median': row['overall_median'] * 1000,
                    'P95': row['overall_p95'] * 1000,
                    'P99': row['overall_p99'] * 1000
                })
        
        perc_df = pd.DataFrame(percentile_data)
        
        # Create grouped bar plot
        x = np.arange(len(perc_df))
        width = 0.25
        
        ax2.bar(x - width, perc_df['Median'], width, label='Median',
                color=[self.colors[db.lower()] for db in perc_df['Database']], alpha=0.8)
        ax2.bar(x, perc_df['P95'], width, label='P95',
                color=[self.colors[db.lower()] for db in perc_df['Database']], alpha=0.6)
        ax2.bar(x + width, perc_df['P99'], width, label='P99',
                color=[self.colors[db.lower()] for db in perc_df['Database']], alpha=0.4)
        
        ax2.set_xlabel('Database')
        ax2.set_ylabel('Latency (ms)')
        ax2.set_title('Latency Percentiles Comparison', fontsize=16, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(perc_df['Database'])
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Load test distribution saved to {save_path}")
        plt.close()
    
    def plot_substring_search_comparison(self, save_path: str = "results/substring_search_comparison.png"):
        """Create bar plots comparing substring search performance"""
        results = self.load_results("substring_search")
        
        if not results:
            logger.error("No substring search results found")
            return
        
        # Calculate average performance across all substrings
        avg_performance = {}
        for db, df in results.items():
            if not df.empty:
                avg_performance[db] = {
                    'mean': df['mean_latency'].mean() * 1000,
                    'p95': df['p95_latency'].mean() * 1000,
                    'p99': df['p99_latency'].mean() * 1000
                }
        
        if not avg_performance:
            logger.error("No valid substring search data found")
            return
        
        # Create bar plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        databases = list(avg_performance.keys())
        x = np.arange(len(databases))
        width = 0.25
        
        means = [avg_performance[db]['mean'] for db in databases]
        p95s = [avg_performance[db]['p95'] for db in databases]
        p99s = [avg_performance[db]['p99'] for db in databases]
        
        bars1 = ax.bar(x - width, means, width, label='Mean',
                       color=[self.colors[db] for db in databases], alpha=0.8)
        bars2 = ax.bar(x, p95s, width, label='P95',
                       color=[self.colors[db] for db in databases], alpha=0.6)
        bars3 = ax.bar(x + width, p99s, width, label='P99',
                       color=[self.colors[db] for db in databases], alpha=0.4)
        
        # Add value labels on bars
        for bars in [bars1, bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.1f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),  # 3 points vertical offset
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=9)
        
        ax.set_xlabel('Database')
        ax.set_ylabel('Average Substring Search Latency (ms)')
        ax.set_title('Substring Search Performance Comparison', fontsize=16, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([db.upper() for db in databases])
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Substring search comparison saved to {save_path}")
        plt.close()
    
    def generate_summary_table(self, save_path: str = "results/summary_table.md"):
        """Generate a markdown summary table with all key metrics"""
        # Load all results
        scalability = self.load_results("scalability")
        load_summary = self.load_results("load_test_summary")
        substring = self.load_results("substring_search")
        
        # Prepare summary data
        summary_data = []
        
        for db in self.databases:
            row = {'Database': db.upper()}
            
            # Scalability metrics (at max records)
            if db in scalability and not scalability[db].empty:
                last_row = scalability[db].iloc[-1]
                row['Max Records'] = f"{last_row['records_in_db']:,}"
                row['Final Query Latency (ms)'] = f"{last_row['query_mean_latency'] * 1000:.2f}"
            else:
                row['Max Records'] = 'N/A'
                row['Final Query Latency (ms)'] = 'N/A'
            
            # Load test metrics
            if db in load_summary and not load_summary[db].empty:
                summary = load_summary[db].iloc[0]
                row['Load Test Mean (ms)'] = f"{summary['overall_mean'] * 1000:.2f}"
                row['Load Test P95 (ms)'] = f"{summary['overall_p95'] * 1000:.2f}"
                row['Load Test P99 (ms)'] = f"{summary['overall_p99'] * 1000:.2f}"
            else:
                row['Load Test Mean (ms)'] = 'N/A'
                row['Load Test P95 (ms)'] = 'N/A'
                row['Load Test P99 (ms)'] = 'N/A'
            
            # Substring search metrics
            if db in substring and not substring[db].empty:
                avg_latency = substring[db]['mean_latency'].mean() * 1000
                row['Substring Search Mean (ms)'] = f"{avg_latency:.2f}"
            else:
                row['Substring Search Mean (ms)'] = 'N/A'
            
            summary_data.append(row)
        
        # Create DataFrame and save as markdown
        summary_df = pd.DataFrame(summary_data)
        
        # Generate markdown table
        markdown_table = "# Database Benchmark Results Summary\n\n"
        markdown_table += "## Test Configuration\n"
        markdown_table += "- **Scalability Test**: Measure performance as database grows (1000 records per batch)\n"
        markdown_table += "- **Load Test**: 1000 iterations of 50 queries (20-30 records each) on fully populated database\n"
        markdown_table += "- **Substring Search**: Search for substring patterns in 'cliente' field\n\n"
        markdown_table += "## Results\n\n"
        markdown_table += tabulate(summary_df, headers='keys', tablefmt='github', showindex=False)
        markdown_table += "\n\n## Performance Rankings\n\n"
        
        # Add rankings based on load test mean latency
        valid_dbs = [(db, float(row['Load Test Mean (ms)'])) 
                     for db, row in zip(summary_df['Database'], summary_data) 
                     if row['Load Test Mean (ms)'] != 'N/A']
        
        if valid_dbs:
            valid_dbs.sort(key=lambda x: x[1])
            markdown_table += "### By Load Test Performance (Mean Latency)\n"
            for i, (db, latency) in enumerate(valid_dbs, 1):
                markdown_table += f"{i}. **{db}**: {latency:.2f} ms\n"
        
        # Save markdown file
        with open(save_path, 'w') as f:
            f.write(markdown_table)
        
        logger.info(f"Summary table saved to {save_path}")
        
        # Also print to console
        print("\n" + markdown_table)
    
    def generate_all_visualizations(self):
        """Generate all visualizations and summary"""
        logger.info("Generating all visualizations...")
        
        # Create output directory if it doesn't exist
        output_dir = Path("results/visualizations")
        output_dir.mkdir(exist_ok=True)
        
        # Generate plots
        self.plot_scalability_comparison(output_dir / "scalability_comparison.png")
        self.plot_load_test_distribution(output_dir / "load_test_distribution.png")
        self.plot_substring_search_comparison(output_dir / "substring_search_comparison.png")
        
        # Generate summary table
        self.generate_summary_table(output_dir / "summary_table.md")
        
        logger.info("All visualizations completed!")


@click.command()
@click.option('--results-dir', default='results', help='Directory containing result CSV files')
@click.option('--output-dir', default='results/visualizations', help='Directory to save visualizations')
def main(results_dir, output_dir):
    """Analyze and visualize benchmark results"""
    analyzer = ResultsAnalyzer(results_dir)
    analyzer.generate_all_visualizations()


if __name__ == '__main__':
    main() 