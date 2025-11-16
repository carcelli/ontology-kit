#!/usr/bin/env python3
"""
Agent Kit Web Demo - Streamlit Application

A simple web interface to demonstrate Agent Kit capabilities.
Deployable on Vercel, Heroku, or any Python hosting platform.
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

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
    "⚙️ Agent Playground"
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

# Footer
st.markdown("---")
st.markdown("""
**Agent Kit** - Democratizing ML for Small Businesses

Built with ❤️ using Streamlit, RDFLib, FAISS, and ontology-driven AI agents.
""")

if __name__ == "__main__":
    # This allows running locally with: streamlit run web_app.py
    pass
