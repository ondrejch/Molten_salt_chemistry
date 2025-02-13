import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.colors import to_rgba
import matplotlib.colors as mcolors

def get_colors_with_repeats(n):
    """Generate colors, allowing repeats but tracking repetition"""
    base_colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    
    colors = []
    color_usage = {}  # Track how many times each color is used
    
    for i in range(n):
        color = base_colors[i % len(base_colors)]
        if color not in color_usage:
            color_usage[color] = 1
        else:
            color_usage[color] += 1
        colors.append((color, color_usage[color]))
    
    return colors

def create_base_patterns():
    """Create a set of distinct patterns with increased density"""
    # Using doubled patterns for increased density
    return ['/////', '\\\\\\\\\\', '|||||', '-----', '+++++', 'xxxxx', 'ooooo', 'OOOOO', '.....']

def plot_surrogate_periodic_table(
    csv_file: str,
    output_filename: str = 'Surrogate_periodic_table.png',
    figsize: tuple = (20, 12)
):
    # Read the data
    from bokeh.sampledata.periodic_table import elements
    df = pd.read_csv(csv_file)
    
    # Get unique surrogates
    unique_surrogates = df['Surrogate'].dropna().unique()
    n_surrogates = len(unique_surrogates)
    
    # Generate colors with usage count
    colors_with_counts = get_colors_with_repeats(n_surrogates)
    patterns = create_base_patterns()
    
    # Create mappings for surrogates
    surrogate_styles = {}
    for i, surrogate in enumerate(unique_surrogates):
        color, usage_count = colors_with_counts[i]
        surrogate_styles[surrogate] = {
            'color': color,
            'pattern': patterns[i % len(patterns)] if usage_count > 1 else None,
            'alpha': 0.9
        }
    
    # Create lighter versions for non-self elements
    element_styles = {}
    for surrogate, style in surrogate_styles.items():
        # Convert hex to RGB and create lighter version
        rgb = np.array(mcolors.to_rgb(style['color']))
        lighter_rgb = 1 - ((1 - rgb) * 0.7)  # Reduced lightening factor from 1.0 to 0.7
        element_styles[surrogate] = {
            'color': mcolors.to_hex(lighter_rgb),
            'pattern': style['pattern'],
            'alpha': style['alpha'] * 0.9  # Slightly reduced alpha for better pattern visibility
        }
    
    # Match quality colors
    match_quality_colors = {
        'self': '#000000',
        'Good': '#4CAF50',
        'Decent': '#FFA500',
        'Poor': '#FF0000'
    }
    
    # Create figure
    fig = plt.figure(figsize=figsize, facecolor='white')
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
    
    # Handle Lanthanides and Actinides
    lanthanides = elements[
        (elements['atomic number'] >= 57) & 
        (elements['atomic number'] <= 71)
    ]['symbol'].tolist()

    actinides = elements[
        (elements['atomic number'] >= 89) & 
        (elements['atomic number'] <= 103)
    ]['symbol'].tolist()

    # Plot elements
    for idx, row in elements.iterrows():
        symbol = row['symbol']
        
        try:
            group = int(row['group']) - 1 if row['group'] != '-' else None
            period = int(row['period']) - 1 if row['period'] != '-' else None
        except (ValueError, TypeError):
            group = None
            period = None

        if symbol in lanthanides:
            period = 8
            group = lanthanides.index(symbol)
        elif symbol in actinides:
            period = 9
            group = actinides.index(symbol)

        if group is not None and period is not None:
            element_data = df[df['Symbol'] == symbol]
            
            if not element_data.empty:
                surrogate = element_data['Surrogate'].iloc[0]
                match_quality = element_data['Match_Quality'].iloc[0]
                
                if pd.isna(surrogate):
                    element_color = '#CCCCCC'
                    pattern = None
                    alpha = 0.9
                    line_width = 1
                else:
                    is_self = isinstance(match_quality, str) and match_quality.lower() == 'self'
                    if is_self:
                        style = surrogate_styles.get(surrogate, {})
                        element_color = style.get('color', '#CCCCCC')
                        pattern = style.get('pattern')
                        alpha = style.get('alpha', 0.9)
                        line_width = 2
                    else:
                        style = element_styles.get(surrogate, {})
                        element_color = style.get('color', '#CCCCCC')
                        pattern = style.get('pattern')
                        alpha = style.get('alpha', 0.9)
                        line_width = 1
                
                # Create element box with color
                rect = Rectangle((group-0.5, period-0.5), 1, 1,
                               facecolor=element_color,
                               edgecolor='black',
                               linewidth=line_width,
                               alpha=alpha)
                ax.add_patch(rect)
                
                # Add pattern with darker color and increased density
                if pattern:
                    ax.add_patch(Rectangle((group-0.5, period-0.5), 1, 1,
                                         hatch=pattern,
                                         fill=False,
                                         alpha=1.0,  # Increased alpha for patterns
                                         edgecolor='#333333'))  # Darker pattern color
                
                # Add match quality indicators
                if pd.isna(match_quality):
                    pass
                elif isinstance(match_quality, str) and match_quality.lower() == 'self':
                    bar = Rectangle((group-0.4, period-0.4), 0.8, 0.05,
                                  facecolor=match_quality_colors['self'],
                                  edgecolor='none',
                                  linewidth=1)
                    ax.add_patch(bar)
                else:
                    quality_str = str(match_quality)
                    quality_color = match_quality_colors.get(quality_str, 'gray')
                    indicator = Circle((group+0.3, period-0.3), 0.1,
                                    facecolor=quality_color,
                                    edgecolor='black',
                                    linewidth=1)
                    ax.add_patch(indicator)

                # Add element text
                ax.text(group, period, symbol,
                       ha='center', va='center',
                       fontweight='bold', fontsize=12,
                       color='black')
                
                ax.text(group, period+0.3, str(row['atomic number']),
                       ha='center', va='center',
                       fontsize=9, color='black')

    # Set plot limits
    ax.set_xlim(-1, 20)
    ax.set_ylim(10, -1)
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Create legend
    legend_elements = [
        Rectangle((0, 0), 1, 1, facecolor=match_quality_colors['self'],
                 label='Self-representing', linewidth=0.5),
        Circle((0, 0), 1, facecolor=match_quality_colors['Good'],
               label='Good Match'),
        Circle((0, 0), 1, facecolor=match_quality_colors['Decent'],
               label='Decent Match'),
        Circle((0, 0), 1, facecolor=match_quality_colors['Poor'],
               label='Poor Match')
    ]
    
    # Add examples of surrogate styles to legend
    for surrogate in unique_surrogates:
        style = surrogate_styles[surrogate]
        patch = Rectangle((0, 0), 1, 1, 
                         facecolor=style['color'],
                         hatch=style['pattern'] if style['pattern'] else '',
                         alpha=style['alpha'],
                         label=f'Surrogate: {surrogate}')
        legend_elements.append(patch)
    
    ax.legend(handles=legend_elements, 
             loc='center left',
             title='Legend',
             bbox_to_anchor=(1.15, 0.5))
    
    plt.title('Periodic Table - Surrogate Elements and Match Quality',
             pad=20, fontweight='bold', fontsize=14)
    
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Surrogate periodic table saved to {output_filename}")

# Example usage
plot_surrogate_periodic_table('PubChemElements_with_surrogates.csv')