from crewai import Agent, Task, Crew, Process
import os
# from crewai_tools import SerperDevTool

class MuseumScavengerHuntCrew:
    def __init__(self):
        os.environ['HF_TOKEN'] = os.environ.get("HF_TOKEN") or os.environ["HF_TOKEN"]
        self.llm = "huggingface/mistralai/Mixtral-8x7B-Instruct-v0.1"
        # search_tool = SerperDevTool(serper_api_key=os.environ["SERPER_API_KEY"] or os.environ.get("SERPER_API_KEY"))
        
        # Create Museum Curator Agent
        self.museum_curator = Agent(
            role='Museum Curator',
            goal='Search for exhibitions and CURRENTLY ON VIEW AS OF TODAY displayed artworks in the given museum website',
            backstory="""Expert museum curator with extensive knowledge of the request museum collection. 
            Specializes in identifying PERMANENT AND CURRENT collection, and notable artworks CURRENTLY on view.""",
            llm=self.llm,
            # tools=[search_tool],
            verbose=True
        )
        
        # Create Art Selector Agent
        self.art_selector = Agent(
            role='Art Selector',
            goal='Select the most famous and interesting artworks in selected museum website for a scavenger hunt',
            backstory="""Art expert who identifies the most significant, visually striking, and 
            historically important artworks in the museum's collection CURRENTLY ON VIEW AT THAT MUSEUM. Can curate a diverse selection 
            that spans different periods, styles, and mediums to create an engaging experience.""",
            llm=self.llm,
            # tools=[search_tool],
            verbose=True
        )
        
        # Create Art Historian Agent
        self.art_historian = Agent(
            role='Art Historian',
            goal='Provide historical context and background for selected artworks',
            backstory="""Expert art historian specialized in analyzing artworks across all periods and styles. 
            Provides insights on artist biography, historical context, techniques, cultural significance, 
            and symbolic meaning.""",
            llm=self.llm,
            # tools=[search_tool],
            verbose=True
        )
        
        # Create Scene Describer Agent
        self.scene_describer = Agent(
            role='Scene Describer',
            goal='Create engaging and detailed descriptions of each artwork',
            backstory="""Skilled at creating vivid, engaging descriptions of artworks that combine 
            historical context with visual details. Excels at highlighting noteworthy elements and 
            creating clues that can be used in a scavenger hunt format.""",
            llm=self.llm,
            verbose=True
        )
    
    async def run_crew(self, museum_name, num_items=5):
        try:
            yield {"type": "start", "step_desc": "Starting generation of scavenger hunt", "message": f"Generating scavenger hunt for: {museum_name}"}
            
            # Task 1: Search museum exhibitions and collections
            yield {"type": "progress", "step_desc": "Searching museum collections", "message": "Researching exhibitions and currently displayed artworks..."}
            
            museum_search_task = Task(
                description=f"""Research the {museum_name} to identify current exhibitions and permanent collections that are on view.
                Focus on identifying galleries, wings, or exhibition areas that contain notable artworks.
                Provide a comprehensive overview of what visitors can currently see in the museum.
                Please be sure to find only current and permanent works on view.""",
                agent=self.museum_curator,
                expected_output="A detailed list of permanent exhibitions and collections on view at the museum"
            )
            
            # Task 2: Select artworks for scavenger hunt
            artwork_selection_task = Task(
                description=f"""Based on the museum research, select exactly {num_items} of the most famous, 
                interesting, and diverse artworks for a scavenger hunt. 
                Choose works that span different time periods, styles, and media when possible.
                For each artwork, include its title, artist, location in the museum, and a brief description.
                Only select artworks that are currently confirmed to be on view.""",
                agent=self.art_selector,
                context=[museum_search_task],
                expected_output=f"A curated list of {num_items} artworks with their basic information"
            )
            
            # Task 3: Provide historical contex
            yield {"type": "progress", "step_desc": "Researching historical context", "message": "Gathering historical and cultural context for artworks..."}
            
            historical_context_task = Task(
                description=f"""For each of the exactly {num_items} artworks, provide rich historical context including:
                1. Artist biography and significance
                2. Historical period and cultural context
                3. Artistic techniques and innovations
                4. Symbolic elements and their meanings
                5. Historical significance and influence""",
                agent=self.art_historian,
                context=[artwork_selection_task],
                expected_output="Interesting historical context, brief artist biography, artistic techniques, and symbolism for each artwork"
            )
            
            # Task 4: Create descriptive scavenger hunt clues (now depends on verification task)
            yield {"type": "progress", "step_desc": "Creating scavenger hunt clues", "message": "Crafting engaging descriptions and clues for verified artworks..."}
            
            scavenger_hunt_task = Task(
                description=f"""Format the response as a numbered scavenger hunt with items equal to exactly {num_items} artworks.
                For each item, prefix the Item Title with an emoji.
                Format your response following OUTLINE below per each artwork. Your response should be easily legibile, with an emoji prefix and one main bullet point for (1) in OUTLINE and sub-bullet points for (2-4) in OUTLINE.
                Each artwork should have following OUTLINE: <
                (1) [Title] by [Artist]
                \n
                (2) Location: [GENERALIZED location information to help visitors navigate to the artwork]
                \n
                (3) Historical Context: [The historical context provided in the previous step. EMPHASIZE SYMBOLS IN THE WORK.]
                \n
                (4) What to Look For: [A vivid description of the scene or artwork]>

                Only include artworks that have been confirmed to be on view or have acceptable substitutes.""",
                agent=self.scene_describer,
                context=[artwork_selection_task],
                expected_output="A complete scavenger hunt with verified artworks"
            )
            
            # Create and run the crew
            crew = Crew(
                agents=[self.museum_curator, self.art_selector, self.art_historian, self.scene_describer],
                tasks=[museum_search_task, artwork_selection_task, historical_context_task, scavenger_hunt_task],
                verbose=True,
                process=Process.sequential
            )
            
            crew_output = crew.kickoff()
            
            if crew_output and crew_output.tasks_output:
                # Get individual task outputs
                museum_info = str(crew_output.tasks_output[0].raw)
                selected_artworks = str(crew_output.tasks_output[1].raw)
                historical_context = str(crew_output.tasks_output[2].raw)
                scavenger_hunt = str(crew_output.tasks_output[3].raw)
                
                # Format the scavenger hunt items
                formatted_hunt = []
                for item in scavenger_hunt.split("\n"):
                    item = item.strip()
                    if not item:
                        continue
                        
                    # Format main item title (starts with number)
                    if any(char.isdigit() for char in item[:2]):
                        formatted_hunt.append(f"\n {item}")
                    # Format location, historical context, and what to look for sections
                    elif item.startswith(("Location:", "Historical Context:", "What to Look For:")):
                        formatted_hunt.append(f"\n {item}")
                    # Format other content as regular text with proper indentation
                    else:
                        formatted_hunt.append(item)

                formatted_scavenger_hunt = "\n".join(formatted_hunt)

                combined_output = f"""# Museum Scavenger Hunt: {museum_name}

## 🏛️ About This Scavenger Hunt
This scavenger hunt features verified artworks from the 🎨 {museum_name}. Each item includes historical context, a description, and clues to help you find the artwork.

## 🔍 Scavenger Hunt Items
{formatted_scavenger_hunt}

---
*Generated using HuggingFace and CrewAI. AI-generated output can be incorrect. *
"""
                
                yield {"type": "complete", "step_desc": "Completed scavenger hunt generation", "message": combined_output}
            else:
                yield {"type": "error", "step_desc": "Error encountered. No scavenger hunt generated", "message": "No scavenger hunt could be generated for this museum."}
                
        except Exception as e:
            yield {"type": "error", "step_desc": "Exception caught","message": f"Error generating scavenger hunt: {str(e)}"}