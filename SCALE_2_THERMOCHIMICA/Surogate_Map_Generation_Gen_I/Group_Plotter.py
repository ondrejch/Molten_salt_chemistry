import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.colors import to_rgba
import matplotlib.colors as mcolors

def get_bright_colors(n):
    """Generate bright colors without dark colors like black or brown"""
    bright_colors = [
        '#1f77b4',  # blue
        '#ff7f0e',  # orange
        '#2ca02c',  # green
        '#d62728',  # red
        '#9467bd',  # purple
        '#e377c2',  # pink
        '#bcbd22',  # yellow-green
        '#17becf',  # cyan
        '#ff9896',  # light red
        '#98df8a',  # light green
        '#ffbb78',  # light orange
        '#aec7e8',  # light blue
        '#f7b6d2',  # light pink
        '#c5b0d5',  # light purple
        '#c49c94'   # light brown (instead of dark brown)
    ]
    
    colors = []
    for i in range(n):
        colors.append(bright_colors[i % len(bright_colors)])
    
    return colors

def is_alkali_or_alkaline_earth(element):
    """Check if element is alkali metal or alkaline earth metal"""
    try:
        group = int(element['group']) if element['group'] != '-' else 0
        return group in [1, 2]
    except (ValueError, TypeError):
        return False

def is_transition_metal(element):
    """Check if element is a transition metal"""
    try:
        group = int(element['group']) if element['group'] != '-' else 0
        period = int(element['period']) if element['period'] != '-' else 0
        # Transition metals are in groups 3-12
        return 3 <= group <= 12 and period >= 4
    except (ValueError, TypeError):
        return False

def is_halide_or_noble_gas(element):
    """Check if element is a halide or noble gas"""
    try:
        group = int(element['group']) if element['group'] != '-' else 0
        return group in [17, 18]  # Group 17 (halogens) and 18 (noble gases)
    except (ValueError, TypeError):
        return False

def is_lanthanide_or_actinide(element):
    """Check if element is a lanthanide or actinide"""
    atomic_num = element['atomic number']
    return (57 <= atomic_num <= 71) or (89 <= atomic_num <= 103)

def plot_element_group(
    csv_file: str,
    group_name: str,
    group_filter_func,
    output_filename: str,
    figsize: tuple = (20, 12)
):
    """Plot a specific group of elements from the periodic table"""
    # Read the data
    from bokeh.sampledata.periodic_table import elements
    df = pd.read_csv(csv_file)
    
    # First, identify which elements are in our focus group
    focus_elements = [row['symbol'] for idx, row in elements.iterrows() if group_filter_func(row)]
    
    # Find all surrogates for our focus elements
    focus_surrogates = df[df['Symbol'].isin(focus_elements)]['Surrogate'].dropna().unique()
    
    # Keep track of which elements should be included (have a relevant surrogate)
    # and which should be left white
    elements_to_include = set()
    
    # Add focus elements and their candidates
    for surrogate in focus_surrogates:
        # Find all elements where this surrogate is used
        elements_with_surrogate = df[df['Surrogate'] == surrogate]['Symbol'].tolist()
        elements_to_include.update(elements_with_surrogate)
    
    # Check if elements from focus group have surrogates outside of focus group
    # If so, don't include them in this graphic
    for symbol in focus_elements:
        element_data = df[df['Symbol'] == symbol]
        if not element_data.empty:
            surrogate = element_data['Surrogate'].iloc[0]
            if pd.notna(surrogate) and surrogate not in focus_surrogates:
                # This element has a surrogate not in our focus group
                # So we should not include it in this graphic
                if symbol in elements_to_include:
                    elements_to_include.remove(symbol)
    
    # Get all surrogates used by our selected elements
    all_surrogates = focus_surrogates
    colors = get_bright_colors(len(all_surrogates))
    
    # Create surrogate to color mapping
    surrogate_colors = {surrogate: colors[i] for i, surrogate in enumerate(all_surrogates)}
    
    # Match quality colors - using black for self
    match_quality_colors = {
        'self': '#000000',  # Black as requested
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
            # Default to white for non-relevant elements
            element_color = '#FFFFFF'  # White
            line_width = 1
            alpha = 0.9
            
            # Get element data
            element_data = df[df['Symbol'] == symbol]
            display_element = False
            
            # Should we display this element?
            if symbol in elements_to_include and not element_data.empty:
                surrogate = element_data['Surrogate'].iloc[0]
                match_quality = element_data['Match_Quality'].iloc[0]
                
                # If has a surrogate and the surrogate is relevant to our focus group
                if pd.notna(surrogate) and surrogate in focus_surrogates:
                    is_self = isinstance(match_quality, str) and match_quality.lower() == 'self'
                    
                    # Get color from the surrogate
                    element_color = surrogate_colors.get(surrogate, '#CCCCCC')
                    
                    # Make self-elements stand out with thicker border
                    if is_self:
                        line_width = 2
                    else:
                        line_width = 1
                    
                    display_element = True
            
            # Create element box with color if we should display it
            if display_element:
                rect = Rectangle((group-0.5, period-0.5), 1, 1,
                               facecolor=element_color,
                               edgecolor='black',
                               linewidth=line_width,
                               alpha=alpha)
                ax.add_patch(rect)
                
                # Add match quality indicators for all elements in this graphic
                if not element_data.empty:
                    match_quality = element_data['Match_Quality'].iloc[0]
                    
                    if pd.notna(match_quality):
                        if isinstance(match_quality, str) and match_quality.lower() == 'self':
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
            else:
                # Just draw a white box with border
                rect = Rectangle((group-0.5, period-0.5), 1, 1,
                               facecolor='#FFFFFF',
                               edgecolor='black',
                               linewidth=1)
                ax.add_patch(rect)

            # Add element text for all elements
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
    
    # Create legend for quality indicators
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
    
    # Add surrogates to the legend
    for surrogate in focus_surrogates:
        color = surrogate_colors[surrogate]
        patch = Rectangle((0, 0), 1, 1, 
                         facecolor=color,
                         alpha=0.9,
                         label=f'Surrogate: {surrogate}')
        legend_elements.append(patch)
    
    ax.legend(handles=legend_elements, 
             loc='center left',
             title='Legend',
             bbox_to_anchor=(1.15, 0.5))
    
    plt.title(f'{group_name} - Surrogate Elements and Match Quality',
             pad=20, fontweight='bold', fontsize=14)
    
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"{group_name} periodic table saved to {output_filename}")

def plot_all_element_groups(csv_file):
    """Create all four periodic table plots with different element groups"""
    # Plot alkali and alkaline earth metals
    plot_element_group(
        csv_file,
        "Alkali and Alkaline Earth Metals",
        is_alkali_or_alkaline_earth,
        "Alkali_Alkaline_Earth_Surrogates.png"
    )
    
    # Plot transition metals
    plot_element_group(
        csv_file,
        "Transition Metals",
        is_transition_metal,
        "Transition_Metals_Surrogates.png"
    )
    
    # Plot halides and noble gases
    plot_element_group(
        csv_file,
        "Halides and Noble Gases",
        is_halide_or_noble_gas,
        "Halides_Noble_Gases_Surrogates.png"
    )
    
    # Plot lanthanides and actinides
    plot_element_group(
        csv_file,
        "Lanthanides and Actinides",
        is_lanthanide_or_actinide,
        "Lanthanides_Actinides_Surrogates.png"
    )

# Example usage
plot_all_element_groups('PubChemElements_with_surrogates.csv')