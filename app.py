import gradio as gr
import asyncio
from museum_crew import MuseumScavengerHuntCrew
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set default environment variables for HuggingFace Spaces
# These can be set in the Spaces environment variables section
# Initialize crew
crew = MuseumScavengerHuntCrew()

async def generate_scavenger_hunt(museum_name, num_items=5, progress=gr.Progress()):
    """Generate a museum scavenger hunt using the Museum Scavenger Hunt Crew"""
    progress(0, desc="Starting scavenger hunt generation...")
    
    # Placeholder for full output
    full_output = ""
    
    # Track progress for UI updates
    step = 0
    total_steps = 4  # Search, Select, Context, Description
    
    # Use a list to collect updates
    updates = []
    
    try:
        # Collect all updates
        async for update in crew.run_crew(museum_name, num_items):
            step += 1
            progress(step / total_steps, desc=f"Step {step}/{total_steps}: {update['step_desc']}")
            updates.append(update)
        
        # Process the final update
        if updates:
            final_update = updates[-1]
            
            if final_update["type"] == "complete":
                full_output = final_update["message"]
                progress(1.0, desc="Scavenger hunt complete!")
            elif final_update["type"] == "error":
                full_output = f"❌ Error: {final_update['message']}"
                progress(1.0, desc="Generation failed")
        else:
            full_output = "No updates received from the crew."
    
    except Exception as e:
        full_output = f"❌ Unexpected error: {str(e)}"
        progress(1.0, desc="Generation failed")
    
    return full_output

def run_generate_scavenger_hunt(museum_name, num_items=5, progress=gr.Progress()):
    """Synchronous wrapper for the async generate_scavenger_hunt function"""
    return asyncio.run(generate_scavenger_hunt(museum_name, num_items, progress))

# Create the Gradio interface
with gr.Blocks(title="Museum Scavenger Hunt Generator", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🏛️ Museum Scavenger Hunt Generator")
    gr.Markdown("Enter the name of a museum to generate a scavenger hunt featuring its most famous artworks.")
    
    with gr.Row():
        museum_input = gr.Textbox(
            label="Museum Name",
            placeholder="e.g., El Prado",
            lines=1
        )
        num_items = gr.Slider(
            minimum=5,
            maximum=30,
            value=5,
            step=5,
            label="Number of Items"
        )
    
    generate_btn = gr.Button("Generate Scavenger Hunt", variant="primary")
    output = gr.Markdown(label="Scavenger Hunt")
    
    generate_btn.click(
    fn=run_generate_scavenger_hunt,  # Use the synchronous wrapper instead
    inputs=[museum_input, num_items],
    outputs=output)
    
    gr.Examples(
        examples=[
            ["El Prado", 5],
            ["Louvre Museum", 10],
            ["Museo Reina Sofia", 5],
            ["National Gallery, London", 20]
        ],
        inputs=[museum_input, num_items]
    )
    
    gr.Markdown("""
    ### About This Tool
    This Museum Scavenger Hunt Generator creates engaging hunts for museum visitors. The process involves:
    
    1. **Museum Curator**: Researches the museum's exhibitions and on-view collections
    2. **Art Selector**: Identifies the most significant and interesting artworks
    3. **Art Historian**: Provides historical context and background for each selected piece
    4. **Scene Describer**: Creates engaging descriptions that combine context with visual details
    
    Powered by HuggingFace and CrewAI.
    """)

# For HuggingFace Spaces
if __name__ == "__main__":
    app.launch()
