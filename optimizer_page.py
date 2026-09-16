import streamlit as st

from modules.parcel_loader import load_parcel_file
from modules.zone_mapper import assign_zones
from modules.driver_plan import calculate_drivers
from modules.mannheim_optimizer import optimize_mannheim


def render_optimizer():
    st.title("🧠 Python Driver Territory Optimizer")
    st.caption("OR-Tools CP-SAT optimizer — manual driver zones remain hard constraints.")
    st.divider()

    st.subheader("🚚 Today's Resources")
    col1, col2, col3 = st.columns(3)
    with col1:
        acar_drivers = st.selectbox("🔵 ACAR Drivers", list(range(1, 10)), index=3, key="py_acar_drivers")
    with col2:
        legno_drivers = st.selectbox("🟢 LEGNO Drivers", list(range(1, 10)), index=2, key="py_legno_drivers")
    with col3:
        st.metric("Total Drivers", acar_drivers + legno_drivers)

    st.info(f"ACAR: {acar_drivers} drivers  |  LEGNO: {legno_drivers} drivers  |  Total: {acar_drivers + legno_drivers}")
    st.divider()

    st.subheader("📍 Manual Driver Zone Assignment")
    st.write("Assign zones manually. A zone can be assigned to multiple drivers; the optimizer can divide ZIP codes within a shared zone between eligible drivers.")
    all_zones = list(range(1, 10))
    driver_assignments = {}

    st.markdown("### 🔵 ACAR Zone Assignment")
    cols = st.columns(min(acar_drivers, 4))
    for i in range(acar_drivers):
        n = i + 1
        with cols[i % len(cols)]:
            zones = st.multiselect(f"ACAR {n}", all_zones, format_func=lambda z: f"Zone {z}", key=f"py_acar_zones_{n}")
            driver_assignments[f"ACAR {n}"] = {"Team": "ACAR", "Zones": zones}

    st.markdown("### 🟢 LEGNO Zone Assignment")
    cols = st.columns(min(legno_drivers, 4))
    for i in range(legno_drivers):
        n = i + 1
        with cols[i % len(cols)]:
            zones = st.multiselect(f"LEGNO {n}", all_zones, format_func=lambda z: f"Zone {z}", key=f"py_legno_zones_{n}")
            driver_assignments[f"LEGNO {n}"] = {"Team": "LEGNO", "Zones": zones}

    st.divider()
    st.subheader("📋 Current Zone Assignment")
    assignment_rows = []
    for name, settings in driver_assignments.items():
        assignment_rows.append({
            "Driver": name,
            "Team": settings["Team"],
            "Zones": ", ".join(f"Zone {z}" for z in settings["Zones"]) if settings["Zones"] else "No zones assigned",
        })
    st.dataframe(assignment_rows, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📂 Upload Today's Parcel File")
    uploaded_file = st.file_uploader("Upload today's parcel file", type=["xlsx", "xls", "csv"], key="py_parcel_file")
    if uploaded_file is None:
        st.info("Upload the delivery Excel/CSV to see zone and ZIP summaries and run the optimizer.")
        return

    try:
        df = assign_zones(load_parcel_file(uploaded_file))
    except Exception as error:
        st.error("❌ Error loading parcel file.")
        st.exception(error)
        return

    st.success("✅ File loaded successfully")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Packages", len(df))
    with c2:
        st.metric("ZIP codes", df["Receiver Zipcode"].nunique())

    st.subheader("📍 Parcels by Zone")
    zone_counts = df.groupby("zone").size().reset_index(name="Parcels").sort_values("zone")
    zone_counts["Drivers Needed"] = zone_counts["Parcels"].apply(calculate_drivers)
    st.dataframe(zone_counts, use_container_width=True, hide_index=True)

    st.subheader("📮 Parcels by ZIP Code")
    zip_counts = (
        df.groupby(["zone", "Receiver Zipcode"])
        .size()
        .reset_index(name="Parcels")
        .sort_values(["zone", "Parcels"], ascending=[True, False])
    )
    st.dataframe(zip_counts, use_container_width=True, hide_index=True)

    st.divider()
    if st.button("🚀 Create Driver Plan", type="primary", use_container_width=True):
        empty = [d for d, s in driver_assignments.items() if not s["Zones"]]
        if empty:
            st.error("❌ Every driver must have at least one assigned zone.")
            st.write("Missing zones for: " + ", ".join(empty))
            return

        parcel_zones = set(int(z) for z in df["zone"].dropna().unique())
        assigned_zones = set()
        for settings in driver_assignments.values():
            assigned_zones.update(settings["Zones"])
        missing = sorted(parcel_zones - assigned_zones)
        if missing:
            st.error(f"❌ These parcel zones are not assigned to any driver: {missing}")
            return

        with st.spinner("Optimizing ZIP-code territories with OR-Tools CP-SAT..."):
            try:
                plan, information = optimize_mannheim(df, driver_assignments)
            except Exception as error:
                st.error("❌ Optimizer error")
                st.exception(error)
                return

        st.success("✅ Driver plan created successfully")
        a, b, c, d, e = st.columns(5)
        a.metric("Drivers", information["drivers"])
        b.metric("ACAR", information["acar_drivers"])
        c.metric("LEGNO", information["legno_drivers"])
        d.metric("Packages", information["total_parcels"])
        e.metric("Average / Driver", information["average_parcels"])

        st.subheader("📊 Final Driver Plan")
        st.dataframe(plan, use_container_width=True, hide_index=True)

        csv = plan.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Driver Plan CSV", csv, "mannheim_driver_plan.csv", "text/csv", use_container_width=True)

        st.subheader("📋 Driver Details")
        for _, driver in plan.iterrows():
            team_icon = "🔵" if driver["Team"] == "ACAR" else "🟢"
            with st.expander(f"{team_icon} {driver['Driver Name']} — {driver['Parcels']} parcels"):
                st.write(f"**Team:** {driver['Team']}")
                st.write(f"**Assigned Zones:** {driver['Assigned Zones']}")
                st.write(f"**Zones Used:** {driver['Zones Used']}")
                st.write(f"**ZIP Codes:** {driver['ZIP Codes']}")
                st.write(f"**Difference From Average:** {driver['Difference From Average']}")

    with st.expander("📄 View Full Parcel Data"):
        st.dataframe(df, use_container_width=True, hide_index=True)
