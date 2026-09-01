import io 
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from aiogram.types import BufferedInputFile
from matplotlib.ticker import FuncFormatter

def generate_activity_plot(records: list) -> BufferedInputFile:
    df = pd.DataFrame(records, columns=['id', 'date', 'focus_time', 'title', 'author'])
    df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y')
    daily_stats = df.groupby('date')['focus_time'].sum().reset_index()
    daily_stats['date_str'] = daily_stats['date'].dt.strftime('%d.%m')

    plt.figure(figsize=(10,6))
    sns.set_theme(style='whitegrid')

    sns.barplot(data=daily_stats, x='date_str', y='focus_time', palette='mako')

    
    def time_formatter(x, pos):
        hours = int(x) // 60
        minutes = int(x) % 60
        return f"{hours:02d}:{minutes:02d}"

    plt.gca().yaxis.set_major_formatter(FuncFormatter(time_formatter))
    
    plt.title('Daily Focus Time', fontsize=16, pad=15)

    plt.title('Daily Focus Time (minutes)', fontsize=16, pad=15)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Focus Time (min)', fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plot_buffer = io.BytesIO()
    plt.savefig(plot_buffer, format='png', dpi=300)
    plot_buffer.seek(0)

    plt.close()

    return BufferedInputFile(plot_buffer.getvalue(), filename='focus_plot.png')