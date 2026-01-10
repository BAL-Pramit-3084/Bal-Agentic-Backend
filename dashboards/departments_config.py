"""
departments_config.py
=====================
Department-specific configurations for the dashboard system.

This file defines all departments and their specific settings:
- Which KPI categories each department tracks
- Which template to use for each department
- Department status (enabled/disabled)
- Department metadata (name, icon, description)

MODULAR DESIGN:
- Easy to add new departments
- Each department is independent
- No code changes needed to add departments (just config)

CURRENT STATUS:
- ENV (Environment): ✅ FULLY CONFIGURED with real data
- Other 19 departments: ⏸️ READY TO CONFIGURE (placeholders)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from config_modules.config import StorageConfig
import os


# ============================================================================
# DEPARTMENT DATA STRUCTURE
# ============================================================================

@dataclass
class TableDefinition:
    """
    Definition of a single table used by a department.

    Attributes:
        name: Table name (e.g., 'env_kpi_transaction', 'kpi_hr_tat')
        structure_type: 'eav' (Entity-Attribute-Value) or 'normalized' (regular table)
        kpi_categories: For EAV tables - which KPI_DESC values to query
        columns: For normalized tables - which columns exist
        primary_date_column: Which column to use for date filtering
    """
    name: str
    structure_type: str  # 'eav' or 'normalized'
    kpi_categories: Optional[List[str]] = None  # For EAV tables
    columns: Optional[List[str]] = None  # For normalized tables
    primary_date_column: str = "DATE"  # Column to filter by date

    def __post_init__(self):
        """Validate table definition"""
        if self.structure_type not in ['eav', 'normalized']:
            raise ValueError(f"structure_type must be 'eav' or 'normalized', got '{self.structure_type}'")

        if self.structure_type == 'eav' and not self.kpi_categories:
            raise ValueError(f"EAV table '{self.name}' must have kpi_categories defined")


@dataclass
class DepartmentDefinition:
    """
    Complete definition of a department's dashboard configuration.

    FLEXIBLE DESIGN - Supports multiple scenarios:
    1. Single EAV table (like ENV)
    2. Multiple normalized tables (like old HR system)
    3. Mix of EAV and normalized tables

    Attributes:
        id: Unique identifier (e.g., 'env', 'hr', 'safety')
        name: Display name (e.g., 'Environment', 'Human Resources')
        icon: Emoji or icon for UI display
        description: Brief description of department
        enabled: Whether department is active
        tables: List of TableDefinition objects (can be 1 or more)
        template_file: HTML template filename
        func_plant_filter: Optional filter for FUNC_PLANT column
        data_processor: Custom data processor function name (optional)
    """
    id: str
    name: str
    icon: str
    description: str
    enabled: bool
    tables: List[TableDefinition]  # Can have 1+ tables
    template_file: str
    func_plant_filter: Optional[str] = None  # If None, use all plants
    data_processor: Optional[str] = None  # Custom processor if needed

    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.id:
            raise ValueError("Department ID cannot be empty")
        if not self.tables and self.enabled:
            raise ValueError(f"Enabled department '{self.id}' must have at least one table defined")

    @property
    def template_path(self) -> str:
        """Get full path to department's template file"""
        return os.path.join(StorageConfig.TEMPLATES_DIR, self.template_file)

    @property
    def template_exists(self) -> bool:
        """Check if template file exists"""
        return os.path.exists(self.template_path)

    @property
    def table_names(self) -> List[str]:
        """Get list of all table names used by this department"""
        return [table.name for table in self.tables]

    @property
    def has_eav_tables(self) -> bool:
        """Check if department uses any EAV tables"""
        return any(table.structure_type == 'eav' for table in self.tables)

    @property
    def has_normalized_tables(self) -> bool:
        """Check if department uses any normalized tables"""
        return any(table.structure_type == 'normalized' for table in self.tables)

    # BACKWARD COMPATIBILITY: For code expecting kpi_categories
    @property
    def kpi_categories(self) -> List[str]:
        """Get all KPI categories from all EAV tables (backward compatibility)"""
        categories = []
        for table in self.tables:
            if table.structure_type == 'eav' and table.kpi_categories:
                categories.extend(table.kpi_categories)
        return categories


# ============================================================================
# DEPRECATED DEPARTMENTS (OLD CONFIGURATIONS - COMMENTED OUT)
# ============================================================================

# OLD ENVIRONMENT DEPARTMENT (DEPRECATED - EAV format)
# Replaced by new normalized table format at line ~422
# DEPARTMENT_ENV_OLD = DepartmentDefinition(
#     id="env",
#     name="Environment",
#     icon="🌿",
#     description="Environmental monitoring (DEPRECATED - Old EAV format)",
#     enabled=False,
#     tables=[TableDefinition(name="env_kpi_transaction", structure_type="eav", ...)],
#     template_file="env_dashboard.html",
#     func_plant_filter="Balgopalpur",
#     data_processor=None
# )


# ============================================================================
# OTHER DEPARTMENTS (PLACEHOLDERS - READY TO CONFIGURE)
# ============================================================================

# ============================================================================
# OTHER DEPARTMENTS (PLACEHOLDERS - READY TO CONFIGURE)
# ============================================================================


# ============================================================================
# OTHER DEPARTMENTS (EXAMPLES - ALL COMMENTED OUT)
# ============================================================================
# Uncomment and configure each department as you prepare their tables and templates

"""
# EXAMPLE 1: HR Department
DEPARTMENT_HR = DepartmentDefinition(
    id="hr",
    name="Human Resources",
    icon="👥",
    description="HR metrics, recruitment, training, and employee management",
    enabled=False,
    tables=[
        TableDefinition(
            name="hr_kpi_transaction",
            structure_type="eav",
            primary_date_column="DATE",
            kpi_categories=["Recruitment", "Training", "Attendance", "Employee Satisfaction"]
        )
    ],
    template_file="hr_dashboard.html",
    func_plant_filter="Balgopalpur"
)

# EXAMPLE 2: Safety Department
DEPARTMENT_SAFETY = DepartmentDefinition(
    id="safety",
    name="Safety",
    icon="🦺",
    description="Safety incidents, compliance, and workplace safety metrics",
    enabled=False,
    tables=[
        TableDefinition(
            name="kpi_safety_incidents",
            structure_type="normalized",
            primary_date_column="INCIDENT_DATE",
            columns=["INCIDENT_TYPE", "SEVERITY", "DEPARTMENT", "DESCRIPTION"]
        )
    ],
    template_file="safety_dashboard.html",
    func_plant_filter="Balgopalpur"
)

# EXAMPLE 3: Production Department
DEPARTMENT_PRODUCTION = DepartmentDefinition(
    id="production",
    name="Production",
    icon="🏭",
    description="Production metrics, output, efficiency, and quality",
    enabled=False,
    tables=[
        TableDefinition(
            name="production_kpi_transaction",
            structure_type="eav",
            primary_date_column="DATE",
            kpi_categories=["Daily Production", "Furnace Performance"]
        )
    ],
    template_file="production_dashboard.html",
    func_plant_filter="Balgopalpur"
)

# Add more departments as needed...
"""

# ============================================================================
# FURNACE DEPARTMENT (FULLY CONFIGURED)
# ============================================================================

DEPARTMENT_FURNACE = DepartmentDefinition(
    id="furnace",
    name="Furnace Operations",
    icon="🔥",
    description="Ferrochrome furnace production, power consumption, recovery, and operational metrics",
    enabled=True,

    # FURNACE uses TWO normalized tables
    tables=[
        TableDefinition(
            name="kpi_furnace_oper_summary",
            structure_type="normalized",
            primary_date_column="KPI_DATE",
            columns=[
                "KPI_DATE", "FCE_NO", "KPI_NO", "KPI_DESC", "UOM",
                "TD_PLAN", "MTD_PLAN", "TD_ACTUAL", "MTD_ACTUAL",
                "TD_VAR", "MTD_VAR"
            ]
        ),
        TableDefinition(
            name="kpi_furnace_tapping_clock",
            structure_type="normalized",
            primary_date_column="KPI_DATE",
            columns=[
                "KPI_DATE", "FCE_NO", "TAP_NO", "ST_TIME", "ED_TIME",
                "DUR", "TT_INTERVAL", "TTI_MWH", "SLAG_TEMP", "MOULD_TEMP",
                "METAL_OUT", "SLAG_OUT", "REMARKS"
            ]
        )
    ],

    # Template file (we'll create this next)
    template_file="furnace_dashboard.html",

    # No plant filter (all furnaces included)
    func_plant_filter=None,

    # Will use custom data processor
    data_processor="furnace"
)


# ============================================================================
# QUALITY CONTROL DEPARTMENT (FULLY CONFIGURED)
# ============================================================================

DEPARTMENT_QC = DepartmentDefinition(
    id="qc",
    name="Quality Control",
    icon="🔬",
    description="Quality control performance, material testing, despatch analysis, and product quality metrics",
    enabled=True,

    # QC uses SIX normalized tables (mix of daily and monthly data)
    tables=[
        TableDefinition(
            name="kpi_qc_despatch_performance",
            structure_type="normalized",
            primary_date_column="report_date",
            columns=[
                "report_date", "customer", "planned_qty", "actual_qty",
                "variance", "reason", "dept_responsible"
            ]
        ),
        TableDefinition(
            name="kpi_qc_furnace_heat_composite_analysis",
            structure_type="normalized",
            primary_date_column="DATE",
            columns=[
                "FURNACE", "DATE", "HEAT_NO", "RECEIVING_TIME", "REPORTING_TIME"
            ]
        ),
        TableDefinition(
            name="kpi_qc_product_deviation",
            structure_type="normalized",
            primary_date_column="MONTH",  # Special: Monthly data
            columns=[
                "MONTH", "YEAR", "FURNACE_NO", "WEEK", "PROD_QTY_MT",
                "CR_DEVIATION_QTY", "SI_DEVIATION_QTY", "C_DEVIATION_QTY",
                "S_DEVIATION_QTY", "P_DEVIATION_QTY", "TOTAL_DEVIATION_MT",
                "DEFECT_PERCENTAGE", "QUALITY_RATE_PERCENTAGE"
            ]
        ),
        TableDefinition(
            name="kpi_qc_stock_summary",
            structure_type="normalized",
            primary_date_column="report_date",
            columns=[
                "report_date", "product", "os_mt", "td_mt", "rec_qty_mtd",
                "fines_add", "fines_less", "returned", "mtd_despatch", "closing_stock"
            ]
        ),
        TableDefinition(
            name="qm_quality_control",
            structure_type="normalized",
            primary_date_column="QLT_START_DATE",
            columns=[
                "LOT_NUMBER", "PLANT", "MATERIAL_DESC", "MATERIAL_TYPE",
                "ACTUAL_LOT_QUANTITY", "QLT_START_DATE", "QLT_END_DATE"
            ]
        ),
        TableDefinition(
            name="qm_quality_control_result",
            structure_type="normalized",
            primary_date_column=None,  # Joined via LOT_NUMBER
            columns=[
                "LOT_NUMBER", "SHORT_TEXT_INS_CHAR", "RESULTS",
                "MATERIAL_DESC", "PLANT"
            ]
        )
    ],

    # Template file (already uploaded)
    template_file="quality_control_dashboard.html",

    # No plant filter
    func_plant_filter=None,

    # Will use custom data processor
    data_processor="qc"
)

# ============================================================================
# SCM (SUPPLY CHAIN MANAGEMENT) DEPARTMENT (FULLY CONFIGURED)
# ============================================================================

DEPARTMENT_SCM = DepartmentDefinition(
    id="scm",
    name="Supply Chain Management",
    icon="📦",
    description="Purchase Orders, Purchase Requisitions, vendor management, and procurement analytics",
    enabled=True,
    tables=[
        TableDefinition(
            name="scm_purchase_order",
            structure_type="normalized",
            primary_date_column="PO_DATE",
            columns=[
                "PO_NO", "ITEM_NO", "PO_DATE", "VENDOR", "VENDOR_NAME",
                "MATERIAL_NO", "MATERIAL_DESC", "PLANT", "PLANT_NAME",
                "QUANTITY", "UNIT", "NET_PRICE", "NET_ORDER_VALUE",
                "MAT_GROUP_DESC", "ORDER_TYPE_DESC", "STILL_DEL_QTY", "GR_QTY"
            ]
        ),
        TableDefinition(
            name="scm_purchase_requisition",
            structure_type="normalized",
            primary_date_column="REQUISITION_DATE",
            columns=[
                "PR_NUMBER", "PR_ITEM", "REQUISITION_DATE", "STATU",
                "PO_NO", "SHORT_TEXT", "QUANTITY", "MATERIAL_GROUP_DESC",
                "PLANT", "REQUISITIONER", "NET_VALUE"
            ]
        )
    ],
    template_file="scm_dashboard.html",
    func_plant_filter=None,
    data_processor="scm"
)

# ============================================================================
# ENVIRONMENT DEPARTMENT (NEW - 14 NORMALIZED TABLES)
# ============================================================================

DEPARTMENT_ENV = DepartmentDefinition(
    id="env",
    name="Environment",
    icon="🌿",
    description="Environmental monitoring, compliance, CBAM emissions, and sustainability tracking",
    enabled=True,  # ENABLED: New normalized table format

    # ENV uses 14 NORMALIZED tables
    tables=[
        TableDefinition(
            name="kpi_env_food_waste_data",
            structure_type="normalized",
            primary_date_column="DATE"
        ),
        TableDefinition(
            name="kpi_env_stp_water_data",
            structure_type="normalized",
            primary_date_column="DATE"
        ),
        TableDefinition(
            name="env_cbam",
            structure_type="normalized",
            primary_date_column="POSTING_DATE"
        ),
        TableDefinition(
            name="kpi_env_compliance",
            structure_type="normalized",
            primary_date_column="VALID_UPTO"
        ),
        TableDefinition(
            name="kpi_env_compliance_return",
            structure_type="normalized",
            primary_date_column=None
        ),
        TableDefinition(
            name="kpi_env_slag_gcp_dust_data",
            structure_type="normalized",
            primary_date_column="YEAR,MONTH"
        ),
        TableDefinition(
            name="kpi_env_biomedical_waste_data",
            structure_type="normalized",
            primary_date_column="DATE"
        ),
        TableDefinition(
            name="kpi_env_incident_report",
            structure_type="normalized",
            primary_date_column="DATE"
        ),
        TableDefinition(
            name="kpi_env_monitoring_report",
            structure_type="normalized",
            primary_date_column="YEAR,MONTH"
        ),
        TableDefinition(
            name="kpi_env_training_records",
            structure_type="normalized",
            primary_date_column="DATE"
        ),
        TableDefinition(
            name="kpi_env_water_consumption_data",
            structure_type="normalized",
            primary_date_column="DATE"
        ),
        TableDefinition(
            name="kpi_env_horticulture_plantation",
            structure_type="normalized",
            primary_date_column=None
        ),
        TableDefinition(
            name="kpi_env_used_oil_data",
            structure_type="normalized",
            primary_date_column="DATE"
        ),
        TableDefinition(
            name="kpi_env_observation_report",
            structure_type="normalized",
            primary_date_column="DATE"
        ),
    ],

    # Template file
    template_file="env_dashboard.html",

    # Plant filter
    func_plant_filter="Balgopalpur",

    # Data processor - uses custom ENV processor
    data_processor="env"
)

# ============================================================================
# MINES - GEOLOGY & SURVEY DEPARTMENT
# ============================================================================

DEPARTMENT_GEOLOGY = DepartmentDefinition(
    id="geology",
    name="Geology & Survey",
    icon="⛏️",
    description="Mining geology, excavation tracking, ore quality analysis, and production planning",
    enabled=True,

    tables=[
        TableDefinition(
            name="mines_day_wise_excavation",
            structure_type="normalized",
            primary_date_column="Prod_date",
            columns=["Prod_date", "Shift", "Loc_Id", "Variant", "Agency", "No_Of_trips", "Qty"]
        ),
        TableDefinition(
            name="mines_geology_face_sample_analysis",
            structure_type="normalized",
            primary_date_column="Prod_date",
            columns=["Prod_date", "Shift", "Loc_Id", "SAMPLE_ID", "Cr2O3", "FeO", "Ratio"]
        ),
        TableDefinition(
            name="mines_monthly_excavation_plan",
            structure_type="normalized",
            primary_date_column="Prod_Month",
            columns=["Prod_Month", "Loc_Id", "Mode", "Grade", "Tonnage", "Cr2O3_Percentage"]
        ),
        TableDefinition(
            name="mines_daily_excavation_plan",
            structure_type="normalized",
            primary_date_column="Prod_date",
            columns=["Prod_date", "Shift", "Loc_Id", "ORE_QTY", "HG_QTY", "MG_QTY", "LG_QTY"]
        ),
        TableDefinition(
            name="mines_location_master",
            structure_type="normalized",
            primary_date_column=None,
            columns=["Loc_Id", "Loc_Desc", "Status"]
        ),
        TableDefinition(
            name="mines_variant_master",
            structure_type="normalized",
            primary_date_column=None,
            columns=["Variant_Id", "Variant_Desc", "Status"]
        ),
        TableDefinition(
            name="mines_agency_master",
            structure_type="normalized",
            primary_date_column=None,
            columns=["Agency_Id", "Agency_Desc", "Status"]
        ),
    ],

    template_file="geology_survey_dashboard.html",
    func_plant_filter=None,
    data_processor="geology"
)


# ============================================================================
# AUTOMOBILE / FLEET MANAGEMENT DEPARTMENT (FULLY CONFIGURED)
# ============================================================================

DEPARTMENT_AUTOMOBILE = DepartmentDefinition(
    id="automobile",
    name="Fleet Management",
    icon="🚛",
    description="MAN truck fleet telematics, fuel consumption, idle time analysis, and driver performance",
    enabled=True,

    tables=[
        TableDefinition(
            name="truck_reports",
            structure_type="normalized",
            primary_date_column="tripDate",
            columns=[
                "slNo", "tripDate", "vehicle_desc", "engine_hours",
                "in_motion_engine_hours", "idling_engine_hours", "avg_speed",
                "max_speed", "distance", "fuel_consumed", "kmpl",
                "parkings_hours", "initial_fuel_level", "final_fuel_level",
                "total_fillings", "total_drains", "filled", "drained"
            ]
        )
    ],

    template_file="automobile_dashboard.html",
    func_plant_filter=None,
    data_processor="automobile"
)

# ============================================================================
# CRM / SALES & DISTRIBUTION DEPARTMENT (FULLY CONFIGURED)
# ============================================================================

DEPARTMENT_CRM = DepartmentDefinition(
    id="crm",
    name="Sales & Distribution",
    icon="📊",
    description="Sales orders, billing, deliveries, customer management, and marketing analytics",
    enabled=True,
    tables=[
        TableDefinition(
            name="sd_sales_order",
            structure_type="normalized",
            primary_date_column="SO_DATE",
            columns=["SO_NO", "SO_DATE", "SOLD_TO_PARTY_NAME", "ORDER_QUANTITY", "NET_VALUE_INR", "DIST_CHANNEL_NAME"]
        ),
        TableDefinition(
            name="sd_sales_status",
            structure_type="normalized",
            primary_date_column="INV_CREATED_ON",
            columns=["BILLING_DOC_NO", "INV_CREATED_ON", "CUSTOMER_NAME", "NET_WEIGHT", "INV_AMT", "DEST_COUNTRY"]
        ),
        TableDefinition(
            name="sd_outbound_delivery",
            structure_type="normalized",
            primary_date_column="GOODS_ISSUE_DT",
            columns=["DELIVERY_NO", "GOODS_ISSUE_DT", "SOLD_PARTY_NAME", "NET_WEIGHT"]
        ),
    ],
    template_file="sd_dashboard.html",
    func_plant_filter=None,
    data_processor="crm"
)


# ============================================================================
# DEPARTMENT REGISTRY
# ============================================================================

# Master list - All enabled departments
ALL_DEPARTMENTS: Dict[str, DepartmentDefinition] = {
    "furnace": DEPARTMENT_FURNACE,
    "qc": DEPARTMENT_QC,
    "scm": DEPARTMENT_SCM,
    "crm": DEPARTMENT_CRM,
    "env": DEPARTMENT_ENV,         # NEW: Normalized table format (line ~422)
    "geology": DEPARTMENT_GEOLOGY,
    "automobile": DEPARTMENT_AUTOMOBILE,

    # Uncomment these as you configure each department:
    # "hr": DEPARTMENT_HR,
    # "safety": DEPARTMENT_SAFETY,
    # "production": DEPARTMENT_PRODUCTION,
    # ... etc
}

# Alias for easier imports (backward compatibility)
DEPARTMENTS = ALL_DEPARTMENTS
# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_department(dept_id: str) -> Optional[DepartmentDefinition]:
    """
    Get department definition by ID.

    Args:
        dept_id: Department identifier

    Returns:
        DepartmentDefinition if found, None otherwise
    """
    return ALL_DEPARTMENTS.get(dept_id.lower())


def get_enabled_departments() -> Dict[str, DepartmentDefinition]:
    """
    Get all enabled departments.

    Returns:
        Dictionary of enabled departments {id: definition}
    """
    return {
        dept_id: dept
        for dept_id, dept in ALL_DEPARTMENTS.items()
        if dept.enabled
    }


def get_departments_list() -> List[Dict[str, Any]]:
    """
    Get list of all departments with basic info (for API responses).

    Returns:
        List of department info dictionaries
    """
    return [
        {
            "id": dept.id,
            "name": dept.name,
            "icon": dept.icon,
            "description": dept.description,
            "enabled": dept.enabled,
            "template_exists": dept.template_exists,
            "kpi_count": len(dept.kpi_categories)
        }
        for dept in ALL_DEPARTMENTS.values()
    ]


def validate_departments() -> List[str]:
    """
    Validate all department configurations.

    Returns:
        List of validation warnings/errors
    """
    issues = []

    for dept_id, dept in ALL_DEPARTMENTS.items():
        # Check enabled departments have templates
        if dept.enabled and not dept.template_exists:
            issues.append(
                f"⚠️  Department '{dept_id}' is enabled but template "
                f"'{dept.template_file}' not found!"
            )

        # Check enabled departments have KPI categories
        if dept.enabled and dept.has_eav_tables and not dept.kpi_categories:
            issues.append(
                f"⚠️  Department '{dept_id}' is enabled but has no KPI categories defined!"
            )

        # Check for duplicate IDs (shouldn't happen, but good to check)
        if dept_id != dept.id:
            issues.append(
                f"❌ Department key '{dept_id}' doesn't match ID '{dept.id}'!"
            )

    return issues


# ============================================================================
# DEPARTMENT TABLE ACCESS CONTROL
# ============================================================================

def get_department_tables(dept_id: str) -> List[str]:
    """
    Get list of table names allowed for a specific department.

    Args:
        dept_id: Department identifier (e.g., 'furnace', 'qc', 'crm')

    Returns:
        List of table names (without database prefix)
    """
    dept = get_department(dept_id)
    if dept and dept.enabled:
        return dept.table_names
    return []


def get_department_tables_with_db(dept_id: str, database: str = "balcorpdb") -> List[str]:
    """
    Get list of fully qualified table names (database.table) for a department.

    Args:
        dept_id: Department identifier
        database: Database name prefix (default: balcorpdb)

    Returns:
        List of fully qualified table names (e.g., 'balcorpdb.kpi_furnace_oper_summary')
    """
    tables = get_department_tables(dept_id)
    return [f"{database}.{table}" for table in tables]


def get_all_allowed_tables() -> Dict[str, List[str]]:
    """
    Get mapping of all departments to their allowed tables.

    Returns:
        Dictionary {department_id: [table_names]}
    """
    return {
        dept_id: dept.table_names
        for dept_id, dept in ALL_DEPARTMENTS.items()
        if dept.enabled
    }


def get_department_for_table(table_name: str) -> Optional[str]:
    """
    Find which department a table belongs to.

    Args:
        table_name: Table name (with or without database prefix)

    Returns:
        Department ID if found, None otherwise
    """
    # Strip database prefix if present
    clean_name = table_name.split('.')[-1].lower()

    for dept_id, dept in ALL_DEPARTMENTS.items():
        if dept.enabled:
            if clean_name in [t.lower() for t in dept.table_names]:
                return dept_id
    return None


def validate_table_access(table_name: str, department: str) -> tuple[bool, str]:
    """
    Validate if a table can be accessed by a specific department.

    Args:
        table_name: Table name (with or without database prefix)
        department: Department ID attempting to access

    Returns:
        (is_allowed, error_message)
    """
    # Strip database prefix if present
    clean_name = table_name.split('.')[-1].lower()

    # Get allowed tables for department
    allowed_tables = get_department_tables(department)
    allowed_lower = [t.lower() for t in allowed_tables]

    if not allowed_tables:
        return False, f"Department '{department}' not found or has no configured tables"

    if clean_name in allowed_lower:
        return True, ""

    # Find which department the table belongs to (for helpful error message)
    actual_dept = get_department_for_table(clean_name)
    if actual_dept:
        return False, f"Table '{table_name}' belongs to '{actual_dept}' department, not '{department}'"

    return False, f"Table '{table_name}' is not allowed for '{department}' department"


def get_department_table_info(dept_id: str) -> Dict[str, Any]:
    """
    Get detailed table information for a department (for system prompts).

    Args:
        dept_id: Department identifier

    Returns:
        Dictionary with table info including columns and descriptions
    """
    dept = get_department(dept_id)
    if not dept or not dept.enabled:
        return {}

    return {
        "department_id": dept.id,
        "department_name": dept.name,
        "description": dept.description,
        "tables": [
            {
                "name": table.name,
                "structure_type": table.structure_type,
                "primary_date_column": table.primary_date_column,
                "columns": table.columns or []
            }
            for table in dept.tables
        ]
    }


# Department aliases for flexible lookups
DEPARTMENT_ALIASES = {
    "quality": "qc",
    "sales": "crm",
    "supply": "scm",
    "supply_chain": "scm",
    "environment": "env",
    "fleet": "automobile",
    "mining": "geology",
    "mines": "geology",
}


def resolve_department_alias(dept_id: str) -> str:
    """
    Resolve department aliases to canonical department ID.

    Args:
        dept_id: Department identifier or alias

    Returns:
        Canonical department ID
    """
    if not dept_id:
        return ""
    dept_lower = dept_id.lower().strip()
    return DEPARTMENT_ALIASES.get(dept_lower, dept_lower)


# ============================================================================
# INITIALIZATION CHECK
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("DEPARTMENT CONFIGURATION VALIDATION")
    print("=" * 70)

    # Show all departments
    print(f"\n📊 Total Departments Configured: {len(ALL_DEPARTMENTS)}")
    print(f"✅ Enabled Departments: {len(get_enabled_departments())}")
    print(f"⏸️  Disabled Departments: {len(ALL_DEPARTMENTS) - len(get_enabled_departments())}")

    print("\n" + "=" * 70)
    print("DEPARTMENT STATUS:")
    print("=" * 70)

    for dept in ALL_DEPARTMENTS.values():
        status = "✅ ENABLED" if dept.enabled else "⏸️  DISABLED"
        template_status = "✅" if dept.template_exists else "❌"
        kpi_count = len(dept.kpi_categories)

        print(f"{status} | {dept.icon} {dept.name}")
        print(f"        ID: {dept.id}")
        print(f"        Template: {template_status} {dept.template_file}")
        print(f"        KPI Categories: {kpi_count}")
        if dept.enabled and kpi_count > 0:
            for kpi in dept.kpi_categories[:3]:  # Show first 3
                print(f"            - {kpi}")
            if kpi_count > 3:
                print(f"            ... and {kpi_count - 3} more")
        print()

    # Validate
    issues = validate_departments()
    if issues:
        print("=" * 70)
        print("⚠️  VALIDATION ISSUES:")
        print("=" * 70)
        for issue in issues:
            print(f"  {issue}")
    else:
        print("=" * 70)
        print("✅ All department configurations are valid!")
        print("=" * 70)