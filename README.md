# Mannheim Depot Optimizer

Streamlit-hosted logistics planning application backed by GitHub.

## Architecture

- **Streamlit/Python**: application shell and the original OR-Tools CP-SAT optimizer.
- **JavaScript + Leaflet/MapLibre**: smooth live map and driver territory selection. Map clicks happen in the browser and do not trigger a Python rerun.
- **Excel processing**: delivery, pickup and redelivery files are processed in the browser in the Live Map workspace.
- **GitHub**: source of truth.
- **Streamlit Community Cloud**: deployment target.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

In Streamlit Community Cloud, create an app from this repository, branch `main`, entrypoint `app.py`.
