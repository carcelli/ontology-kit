#!/usr/bin/env python3
"""
Agent Kit Web Demo - Streamlit Application

A simple web interface to demonstrate Agent Kit capabilities.
Deployable on Vercel, Heroku, or any Python hosting platform.
"""

import sys
from pathlib import Path

import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def visualize_ontology_network(graph, max_nodes=100):
    """Create a Plotly network graph from RDF graph."""
    nx_graph = nx.DiGraph()

    # Extract triples and limit count
    triples = list(graph)[:max_nodes]

    for s, p, o in triples:
        # Simplify labels
        s_label = str(s).split('#')[-1].split('/')[-1]
        o_label = str(o).split('#')[-1].split('/')[-1]
        nx_graph.add_edge(s_label, o_label, title=str(p).split('#')[-1])

    # Layout
    pos = nx.spring_layout(nx_graph, seed=42)

    # Edges
    edge_x = []
    edge_y = []
    for edge in nx_graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    # Nodes
    node_x = []
    node_y = []
    node_text = []
    node_adjacencies = []

    for node in nx_graph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        node_adjacencies.append(len(nx_graph[node]))

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="top center",
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            reversescale=True,
            color=node_adjacencies,
            size=15,
            colorbar=dict(
                thickness=15,
                title='Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))

    fig = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    title='Ontology Knowledge Graph',
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    return fig

st.set_page_config(
    page_title="Agent Kit - Ontology-Driven ML",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 Agent Kit - Ontology-Driven ML Demo")
st.markdown("---")

# Sidebar navigation
page = st.sidebar.radio("Choose Demo", [
    "🏠 Home",
    "🔍 Ontology Explorer",
    "📊 Vector Search",
    "🎯 Leverage Analysis",
    "⚙️ Agent Playground",
    "📓 Notebooks"
])

if page == "🏠 Home":
    st.header("Welcome to Agent Kit")

    st.markdown("""
    **Agent Kit** is an ontology-driven machine learning framework for small businesses.

    ### 🎯 Key Features
    - **Ontology-Grounded Agents**: Reduce hallucinations with knowledge graphs
    - **Multi-SDK Support**: OpenAI, LangChain, AutoGen integration
    - **Vector Space Navigation**: Semantic search and reasoning
    - **Business Intelligence**: Forecasting, optimization, leverage analysis

    ### 🏗️ Architecture
    ```
    Ontology Layer (RDF/OWL + SPARQL)
           ↓
    Agent Orchestration (Custom + SDK Adapters)
           ↓
    Business Applications (Forecasting, Analytics)
    ```
    """)

    st.info("🚀 This demo showcases Agent Kit capabilities. Select a demo from the sidebar!")

elif page == "🔍 Ontology Explorer":
    st.header("Ontology Explorer")

    st.markdown("Explore the knowledge graphs that power Agent Kit agents.")

    try:
        from agent_kit.ontology.loader import OntologyLoader

        # Load core ontology
        ontology_path = "assets/ontologies/core.ttl"
        if Path(ontology_path).exists():
            try:
                loader = OntologyLoader(ontology_path)
                graph = loader.load()

                # Visualize Graph
                st.subheader("🕸️ Graph Visualization")
                fig = visualize_ontology_network(graph)
                st.plotly_chart(fig, use_container_width=True)

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📊 Ontology Stats")
                    st.metric("Triples", len(list(graph)))
                    st.metric("Namespaces", len(loader.namespaces))

                with col2:
                    st.subheader("🔍 Query Interface")

                    query = st.text_area(
                        "SPARQL Query",
                        "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
                        height=100
                    )

                    if st.button("Execute Query"):
                        try:
                            results = loader.query(query)
                            if results:
                                st.dataframe(results)
                            else:
                                st.info("No results found")
                        except Exception as e:
                            st.error(f"Query error: {e}")
            except Exception as e:
                st.error(f"Failed to load ontology: {e}")
                st.info("This demo requires ontology files to be present.")
        else:
            st.warning("Ontology file not found in deployed environment.")
            st.info("This is normal for the web demo. Full functionality requires local setup.")

    except ImportError as e:
        st.error(f"Import error: {e}. Please install dependencies.")

elif page == "📊 Vector Search":
    st.header("Vector Space Search")

    st.markdown("Demonstrate semantic search capabilities using embeddings and FAISS.")

    try:
        from agent_kit.vectorspace import Embedder, VectorIndex

        st.subheader("🔤 Text Embeddings Demo")

        text_input = st.text_area(
            "Enter text to embed and search:",
            "Small business revenue optimization strategies",
            height=100
        )

        if st.button("Generate Embedding & Search"):
            with st.spinner("Processing..."):
                embedder = Embedder()
                index = VectorIndex(dimension=embedder.dimension)

                # Sample documents for search
                sample_docs = [
                    "Revenue forecasting using machine learning",
                    "Customer acquisition strategies for small businesses",
                    "Inventory optimization techniques",
                    "Cash flow management best practices",
                    "Marketing automation tools",
                    "Business intelligence dashboards",
                    "Supply chain optimization",
                    "Financial planning for startups"
                ]

                # Add sample documents to index
                embeddings = embedder.embed_batch(sample_docs)
                index.add(embeddings, ids=list(range(len(sample_docs))))

                # Search for similar content
                query_vec = embedder.embed(text_input)
                results = index.query(query_vec, k=3)

                st.success("Search completed!")

                for i, result in enumerate(results):
                    st.write(f"**{i+1}.** {sample_docs[result['id']]}")
                    st.write(f"   Similarity: {result['distance']:.3f}")
                    st.write("---")

    except Exception as e:
        st.error(f"Vector search demo error: {e}")

elif page == "🎯 Leverage Analysis":
    st.header("Business Leverage Analysis")

    st.markdown("Analyze leverage points in business ontologies using hyperdimensional visualization.")

    try:
        # This would integrate with the leverage analysis tools
        st.info("Leverage analysis tools available in the full Agent Kit implementation.")

        st.subheader("📈 Sample Leverage Concepts")

        leverage_data = {
            "Concept": ["Pricing Strategy", "Customer Retention", "Inventory Turnover", "Marketing ROI", "Operational Efficiency"],
            "Leverage Score": [0.85, 0.72, 0.68, 0.91, 0.76],
            "Impact Potential": ["High", "Medium", "Medium", "Very High", "High"]
        }

        import pandas as pd
        df = pd.DataFrame(leverage_data)

        # Interactive Plotly Chart
        fig = px.bar(
            df,
            x="Concept",
            y="Leverage Score",
            color="Impact Potential",
            title="Business Leverage Analysis",
            hover_data=["Impact Potential"],
            color_discrete_map={"High": "orange", "Very High": "red", "Medium": "blue"}
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df)

        st.markdown("""
        **How Leverage Analysis Works:**
        1. **Ontology Mapping**: Map business concepts to RDF graph
        2. **Centrality Analysis**: Identify key nodes using betweenness centrality
        3. **Uncertainty Scoring**: Measure prediction confidence
        4. **Impact Ranking**: Combine factors for leverage scores
        """)

    except Exception as e:
        st.error(f"Leverage analysis demo error: {e}")

elif page == "⚙️ Agent Playground":
    st.header("Agent Playground")

    st.markdown("Interact with Agent Kit agents directly.")

    try:
        from agent_kit.agents.business_agents import ForecastAgent

        st.subheader("🎯 Forecast Agent Demo")

        user_input = st.text_area(
            "Describe your forecasting request:",
            "Forecast Q3 revenue for a small bakery business",
            height=100
        )

        if st.button("Run Forecast Agent"):
            with st.spinner("Agent thinking..."):
                try:
                    agent = ForecastAgent()
                    result = agent.run(user_input)

                    st.success("Forecast completed!")

                    st.subheader("Agent Result")
                    st.write(result.result)

                    # Show agent observations if available
                    if hasattr(result, 'observations') and result.observations:
                        st.subheader("Agent Observations")
                        for obs in result.observations:
                            st.write(f"• {obs}")

                except Exception as e:
                    st.error(f"Agent execution error: {e}")

    except ImportError as e:
        st.error(f"Agent import error: {e}. Please install dependencies.")
        st.info("The ForecastAgent requires additional setup and API keys.")

elif page == "📓 Notebooks":
    st.header("Jupyter Notebooks")
    st.markdown("Access interactive notebooks for deeper analysis and experimentation.")

    notebooks = list(Path("examples").glob("*.ipynb"))

    if notebooks:
        st.success(f"Found {len(notebooks)} notebooks in `examples/` directory.")

        for nb in notebooks:
            with st.expander(f"📄 {nb.name}"):
                st.write(f"**Path:** `{nb}`")
                st.code(f"jupyter notebook {nb}", language="bash")

                # Option to convert to HTML for viewing (if nbconvert is installed)
                if st.button(f"Generate HTML Preview for {nb.name}"):
                    try:
                        import subprocess
                        # Convert to html
                        cmd = f"jupyter nbconvert --to html '{nb}' --stdout"
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        if result.returncode == 0:
                            st.components.v1.html(result.stdout, height=600, scrolling=True)
                        else:
                            st.error(f"Conversion failed: {result.stderr}")
                    except Exception as e:
                        st.error(f"Error running nbconvert: {e}")
    else:
        st.info("No notebooks found in `examples/` directory.")
        st.markdown("Create a notebook to get started!")

# Footer
st.markdown("---")
st.markdown("""
**Agent Kit** - Democratizing ML for Small Businesses

Built with ❤️ using Streamlit, RDFLib, FAISS, and ontology-driven AI agents.
""")

if __name__ == "__main__":
    # This allows running locally with: streamlit run web_app.py
    pass
