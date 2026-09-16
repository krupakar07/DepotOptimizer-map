import streamlit as st

from modules.parcel_loader import load_parcel_file
from modules.zone_mapper import assign_zones
from modules.driver_plan import calculate_drivers
from modules.mannheim_optimizer import optimize_mannheim


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Depot Optimizer",
    page_icon="🚚",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title("🚚 Depot Optimizer")
st.write("### Depot Management Dashboard")

st.divider()


# ============================================================
# DRIVER COUNTS
# ============================================================

st.subheader(
    "🚚 Today's Resources"
)

col1, col2, col3 = st.columns(3)


with col1:

    acar_drivers = st.selectbox(
        "🔵 ACAR Drivers",
        options=list(range(1, 10)),
        index=3
    )


with col2:

    legno_drivers = st.selectbox(
        "🟢 LEGNO Drivers",
        options=list(range(1, 10)),
        index=2
    )


with col3:

    total_drivers = (
        acar_drivers
        +
        legno_drivers
    )

    st.metric(
        "Total Drivers",
        total_drivers
    )


st.info(
    f"ACAR: {acar_drivers} drivers  |  "
    f"LEGNO: {legno_drivers} drivers  |  "
    f"Total: {total_drivers} drivers"
)


# ============================================================
# MANUAL ZONE ASSIGNMENT
# ============================================================

st.divider()

st.subheader(
    "📍 Manual Driver Zone Assignment"
)

st.write(
    """
    Assign the zones manually to each driver.
    Zones 1–9 are all available to both ACAR and LEGNO.

    A zone can be assigned to multiple drivers.
    When this happens, the optimizer will divide
    the ZIP codes of that zone between those drivers.
    """
)


ALL_ZONES = list(
    range(1, 10)
)


# ============================================================
# ACAR ZONES
# ============================================================

st.markdown(
    "## 🔵 ACAR Zone Assignment"
)


acar_assignments = {}


acar_columns = st.columns(
    min(acar_drivers, 4)
)


for driver_index in range(
    acar_drivers
):

    driver_number = (
        driver_index + 1
    )

    column = acar_columns[
        driver_index
        %
        len(acar_columns)
    ]

    with column:

        selected_zones = st.multiselect(
            f"ACAR {driver_number}",
            options=ALL_ZONES,
            format_func=lambda zone:
                f"Zone {zone}",
            key=f"acar_zones_{driver_number}"
        )

        acar_assignments[
            f"ACAR {driver_number}"
        ] = {

            "Team":
                "ACAR",

            "Zones":
                selected_zones
        }


# ============================================================
# LEGNO ZONES
# ============================================================

st.markdown(
    "## 🟢 LEGNO Zone Assignment"
)


legno_assignments = {}


legno_columns = st.columns(
    min(legno_drivers, 4)
)


for driver_index in range(
    legno_drivers
):

    driver_number = (
        driver_index + 1
    )

    column = legno_columns[
        driver_index
        %
        len(legno_columns)
    ]

    with column:

        selected_zones = st.multiselect(
            f"LEGNO {driver_number}",
            options=ALL_ZONES,
            format_func=lambda zone:
                f"Zone {zone}",
            key=f"legno_zones_{driver_number}"
        )

        legno_assignments[
            f"LEGNO {driver_number}"
        ] = {

            "Team":
                "LEGNO",

            "Zones":
                selected_zones
        }


# ============================================================
# COMBINE DRIVER ASSIGNMENTS
# ============================================================

driver_assignments = {}

driver_assignments.update(
    acar_assignments
)

driver_assignments.update(
    legno_assignments
)


# ============================================================
# SHOW CURRENT ASSIGNMENTS
# ============================================================

st.divider()

st.subheader(
    "📋 Current Zone Assignment"
)


assignment_rows = []


for driver_name, settings in driver_assignments.items():

    zones = settings[
        "Zones"
    ]

    assignment_rows.append({

        "Driver":
            driver_name,

        "Team":
            settings["Team"],

        "Zones":
            ", ".join(
                f"Zone {zone}"
                for zone in zones
            )
            if zones
            else "No zones assigned"

    })


assignment_preview = st.dataframe(
    assignment_rows,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# FILE UPLOAD
# ============================================================

st.divider()

st.subheader(
    "📂 Upload Today's Parcel File"
)


uploaded_file = st.file_uploader(
    "Upload Today's Parcel File",
    type=[
        "xlsx",
        "xls",
        "csv"
    ]
)


# ============================================================
# PROCESS FILE
# ============================================================

if uploaded_file is not None:

    # ========================================================
    # LOAD PARCEL FILE
    # ========================================================

    try:

        df = load_parcel_file(
            uploaded_file
        )

        df = assign_zones(
            df
        )

    except Exception as error:

        st.error(
            "❌ Error loading parcel file."
        )

        st.exception(
            error
        )

        st.stop()


    st.success(
        "✅ File Loaded Successfully!"
    )


    # ========================================================
    # TOTAL PARCELS
    # ========================================================

    st.subheader(
        "📦 Total Parcels"
    )

    st.metric(
        "Parcels",
        len(df)
    )


    # ========================================================
    # ZONE SUMMARY
    # ========================================================

    st.subheader(
        "📍 Parcels by Zone"
    )


    zone_counts = (
        df.groupby(
            "zone"
        )
        .size()
        .reset_index(
            name="Parcels"
        )
        .sort_values(
            "zone"
        )
    )


    zone_counts[
        "Drivers Needed"
    ] = (
        zone_counts[
            "Parcels"
        ]
        .apply(
            calculate_drivers
        )
    )


    st.dataframe(
        zone_counts,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # ZIP SUMMARY
    # ========================================================

    st.subheader(
        "📮 Parcels by ZIP Code"
    )


    zip_counts = (
        df.groupby(
            [
                "zone",
                "Receiver Zipcode"
            ]
        )
        .size()
        .reset_index(
            name="Parcels"
        )
        .sort_values(
            [
                "zone",
                "Parcels"
            ],
            ascending=[
                True,
                False
            ]
        )
    )


    st.dataframe(
        zip_counts,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # OPTIMIZATION
    # ========================================================

    st.divider()

    st.subheader(
        "🧠 Driver Territory Optimizer"
    )

    st.write(
        """
        The optimizer will respect the zones you manually
        assigned to each driver. It will then distribute
        the ZIP codes between eligible drivers while
        balancing parcel volume.
        """
    )


    # ========================================================
    # CREATE PLAN
    # ========================================================

    if st.button(
        "🚀 Create Driver Plan",
        type="primary",
        use_container_width=True
    ):

        # ====================================================
        # CHECK FOR EMPTY DRIVER ASSIGNMENTS
        # ====================================================

        empty_drivers = [

            driver

            for driver, settings
            in driver_assignments.items()

            if not settings["Zones"]

        ]


        if empty_drivers:

            st.error(
                "❌ The following drivers have no zones assigned:"
            )

            for driver in empty_drivers:

                st.write(
                    f"- {driver}"
                )

            st.stop()


        # ====================================================
        # CHECK THAT PARCEL ZONES ARE COVERED
        # ====================================================

        parcel_zones = set(
            int(zone)
            for zone
            in df["zone"]
            .dropna()
            .unique()
        )


        assigned_zones = set()


        for settings in driver_assignments.values():

            assigned_zones.update(
                settings["Zones"]
            )


        missing_zones = sorted(
            parcel_zones
            -
            assigned_zones
        )


        if missing_zones:

            st.error(
                "❌ These zones contain parcels "
                "but have not been assigned to "
                f"any driver: {missing_zones}"
            )

            st.stop()


        # ====================================================
        # RUN OPTIMIZER
        # ====================================================

        with st.spinner(
            "Optimizing ZIP-code territories..."
        ):

            try:

                plan, information = (
                    optimize_mannheim(
                        df,
                        driver_assignments
                    )
                )

            except Exception as error:

                st.error(
                    "❌ Optimizer error"
                )

                st.exception(
                    error
                )

                st.stop()


        # ====================================================
        # SUCCESS
        # ====================================================

        st.success(
            "✅ Driver plan created successfully!"
        )


        # ====================================================
        # SUMMARY
        # ====================================================

        st.subheader(
            "📊 Plan Summary"
        )


        col1, col2, col3, col4 = st.columns(4)


        with col1:

            st.metric(
                "Total Drivers",
                information[
                    "drivers"
                ]
            )


        with col2:

            st.metric(
                "ACAR Drivers",
                information[
                    "acar_drivers"
                ]
            )


        with col3:

            st.metric(
                "LEGNO Drivers",
                information[
                    "legno_drivers"
                ]
            )


        with col4:

            st.metric(
                "Total Parcels",
                information[
                    "total_parcels"
                ]
            )


        st.metric(
            "Average Parcels / Driver",
            information[
                "average_parcels"
            ]
        )


        # ====================================================
        # ACAR PLAN
        # ====================================================

        acar_plan = plan[
            plan["Team"] == "ACAR"
        ]


        if not acar_plan.empty:

            st.subheader(
                "🔵 ACAR Driver Plan"
            )

            st.dataframe(
                acar_plan,
                use_container_width=True,
                hide_index=True
            )


        # ====================================================
        # LEGNO PLAN
        # ====================================================

        legno_plan = plan[
            plan["Team"] == "LEGNO"
        ]


        if not legno_plan.empty:

            st.subheader(
                "🟢 LEGNO Driver Plan"
            )

            st.dataframe(
                legno_plan,
                use_container_width=True,
                hide_index=True
            )


        # ====================================================
        # DRIVER DETAILS
        # ====================================================

        st.subheader(
            "📋 Driver Details"
        )


        for _, driver in plan.iterrows():

            driver_name = driver[
                "Driver Name"
            ]

            team = driver[
                "Team"
            ]

            assigned_zones = driver[
                "Assigned Zones"
            ]

            zones_used = driver[
                "Zones Used"
            ]

            zipcodes = driver[
                "ZIP Codes"
            ]

            parcels = driver[
                "Parcels"
            ]

            difference = driver[
                "Difference From Average"
            ]


            icon = (
                "🔵"
                if team == "ACAR"
                else "🟢"
            )


            with st.expander(
                f"{icon} {driver_name} "
                f"— {parcels} parcels"
            ):

                st.write(
                    f"**Team:** {team}"
                )

                st.write(
                    f"**Assigned Zones:** "
                    f"{assigned_zones}"
                )

                st.write(
                    f"**Zones Used:** "
                    f"{zones_used}"
                )

                st.write(
                    f"**ZIP Codes:** "
                    f"{zipcodes}"
                )

                st.write(
                    f"**Parcels:** "
                    f"{parcels}"
                )

                st.write(
                    f"**Difference From Average:** "
                    f"{difference}"
                )


    # ========================================================
    # FULL DATA
    # ========================================================

    with st.expander(
        "📄 View Full Parcel Data"
    ):

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )