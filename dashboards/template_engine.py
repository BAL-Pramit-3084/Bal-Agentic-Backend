"""
template_engine.py
==================
Template engine for injecting data into HTML dashboard templates.

This module:
- Loads HTML template files
- Converts processed Python data to JavaScript format
- Injects data into templates (replacing placeholders)
- Handles missing data gracefully
- Generates Chart.js compatible data structures

The challenge: Templates have hardcoded JavaScript data arrays.
The solution: Smart string replacement and JavaScript generation.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from string import Template

from config_modules.config import StorageConfig
from dashboards.departments_config import DepartmentDefinition

# ============================================================================
# LOGGING SETUP
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# JAVASCRIPT DATA GENERATOR
# ============================================================================

class JavaScriptDataGenerator:
    """
    Converts Python data structures to JavaScript code.

    Handles JSON serialization with proper formatting for embedding in HTML.
    """

    @staticmethod
    def to_js_array(data: List[Dict]) -> str:
        """
        Convert Python list of dicts to JavaScript array literal.

        Args:
            data: List of dictionaries

        Returns:
            JavaScript array string
        """
        if not data:
            return "[]"

        # Use JSON with proper formatting
        js_code = json.dumps(data, indent=4, ensure_ascii=False)
        return js_code

    @staticmethod
    def to_js_object(data: Dict) -> str:
        """
        Convert Python dict to JavaScript object literal.

        Args:
            data: Dictionary

        Returns:
            JavaScript object string
        """
        if not data:
            return "{}"

        js_code = json.dumps(data, indent=4, ensure_ascii=False)
        return js_code

    @staticmethod
    def to_js_variable(var_name: str, data: Any) -> str:
        """
        Generate JavaScript variable declaration.

        Args:
            var_name: Variable name
            data: Data to assign (list, dict, or primitive)

        Returns:
            JavaScript variable declaration
        """
        if isinstance(data, list):
            js_value = JavaScriptDataGenerator.to_js_array(data)
        elif isinstance(data, dict):
            js_value = JavaScriptDataGenerator.to_js_object(data)
        else:
            js_value = json.dumps(data)

        return f"const {var_name} = {js_value};"


# ============================================================================
# DATA FORMATTERS FOR SPECIFIC KPI CATEGORIES
# ============================================================================

class KPIDataFormatter:
    """
    Format processed KPI data for template injection.

    Each KPI category may need different formatting for the template.
    """

    @staticmethod
    def format_food_waste(data: List[Dict]) -> List[Dict]:
        """
        Format Food Waste data for template.

        Expected template format:
        {
            location: "Plant Canteen",
            waste: 8.1,
            personsCount: 457,
            wastePerPerson: 17.724,
            unit: "kg",
            perPersonUnit: "gm"
        }
        """
        formatted = []

        for item in data:
            # Get values and handle NULL properly
            location = item.get("Location", "")
            waste = item.get("Waste", "")
            persons = item.get("Persons Count", "")
            waste_per_person = item.get("Waste Per Person", "")

            # Skip completely empty records
            if not location or location.strip() == "":
                continue

            # Convert to appropriate types, handle NULL as 0 for charts
            formatted.append({
                "location": location if location else "Data not available",
                "waste": float(waste) if waste not in [None, "", "NULL"] else 0,
                "personsCount": int(float(persons)) if persons not in [None, "", "NULL"] else 0,
                "wastePerPerson": float(waste_per_person) if waste_per_person not in [None, "", "NULL"] else 0,
                "unit": "kg",
                "perPersonUnit": "gm"
            })

        return formatted

    @staticmethod
    def format_bio_medical_waste(data: List[Dict]) -> List[Dict]:
        """
        Format Bio Medical Waste data for template.

        Expected template format:
        {
            containerType: "Yellow",
            category: "Solid Waste",
            weight: 32.0,
            unit: "gm",
            action: "Generated",
            department: "Medical"
        }
        """
        formatted = []

        for item in data:
            # Get values and handle NULL properly
            container_type = item.get("Container Type", "")
            category = item.get("Waste Category", "")
            weight = item.get("Weight", "")
            action = item.get("Action Type", "")
            department = item.get("Department", "")

            # Skip completely empty records
            if not container_type or container_type.strip() == "":
                continue

            formatted.append({
                "containerType": container_type if container_type else "Data not available",
                "category": category if category else "Data not available",
                "weight": float(weight) if weight not in [None, "", "NULL"] else 0,
                "unit": item.get("Weight_UOM", "gm"),
                "action": action if action else "Data not available",
                "department": department if department else "Data not available"
            })

        return formatted

    @staticmethod
    def format_horticulture(data: List[Dict]) -> List[Dict]:
        """
        Format Horticulture data for template.

        Expected template format:
        {
            area: "MYAZAKI PROJECT AREA",
            species: "COCONUT",
            planted: 50,
            target: 50
        }
        """
        formatted = []

        for item in data:
            area = item.get("Area", "")
            plant_name = item.get("Plant Name", "")
            actual = item.get("Actual")
            target = item.get("Target")

            # Skip completely empty records
            if not area and not plant_name:
                continue

            # Handle None/NaN/empty values
            if actual in [None, "", "NULL"]:
                actual = 0
            if target in [None, "", "NULL"]:
                target = 0

            formatted.append({
                "area": area if area else "Data not available",
                "species": plant_name if plant_name else "Data not available",
                "planted": int(float(actual)) if actual not in [None, "", "NULL", 0] else 0,
                "target": int(float(target)) if target not in [None, "", "NULL", 0] else 0
            })

        return formatted

    @staticmethod
    def format_slag_gcp_dust(data: Dict) -> Dict:
        """
        Format Slag & GCP Dust data for template.

        Expected template format:
        {
            production: 10003.21,
            slag: 10715.715,
            gcpDust: 236.815
        }
        """
        # Handle case where data is a list with single dict (from EAV transformer)
        if isinstance(data, list):
            if len(data) == 0:
                data = {}
            else:
                data = data[0]  # Take first element

        # Handle empty dict
        if not data:
            return {
                "production": 0,
                "slag": 0,
                "gcpDust": 0
            }

        production = data.get("Production", "")
        slag = data.get("Slag", "")
        gcp_dust = data.get("GCP Dust", "")

        return {
            "production": float(production) if production not in [None, "", "NULL"] else 0,
            "slag": float(slag) if slag not in [None, "", "NULL"] else 0,
            "gcpDust": float(gcp_dust) if gcp_dust not in [None, "", "NULL"] else 0
        }

    @staticmethod
    def format_environment_observation(data: List[Dict]) -> List[Dict]:
        """
        Format Environment Observation data for template.
        """
        formatted = []

        for item in data:
            observer = item.get("Observer", "")
            area = item.get("Area", "")
            description = item.get("Description", "")

            # Skip completely empty records
            if not observer and not area:
                continue

            formatted.append({
                "observer": observer if observer else "Data not available",
                "area": area if area else "Data not available",
                "description": description if description else "No description"
            })

        return formatted

    @staticmethod
    def format_environment_incident(data: List[Dict]) -> List[Dict]:
        """
        Format Environment Incident data for template.
        """
        formatted = []

        for item in data:
            emp_id = item.get("Employee ID", "")
            name = item.get("Name", "")
            department = item.get("Department", "")
            description = item.get("Incident Description", "")

            # Skip completely empty records
            if not emp_id and not name:
                continue

            formatted.append({
                "employeeId": emp_id if emp_id else "Data not available",
                "name": name if name else "Data not available",
                "department": department if department else "Data not available",
                "description": description if description else "No description"
            })

        return formatted


# ============================================================================
# TEMPLATE ENGINE
# ============================================================================

class TemplateEngine:
    """
    Main template engine for generating dashboards.

    Loads HTML templates and injects processed data.
    """

    def __init__(self, department: DepartmentDefinition):
        """
        Initialize template engine for a department.

        Args:
            department: DepartmentDefinition object
        """
        self.department = department
        self.template_path = department.template_path

    def load_template(self) -> str:
        """
        Load HTML template from file.

        Returns:
            Template HTML as string
        """
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(
                f"Template not found: {self.template_path}"
            )

        with open(self.template_path, 'r', encoding='utf-8') as f:
            template_html = f.read()

        logger.info(f"Loaded template: {self.template_path}")
        return template_html

    def prepare_template_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data for template injection.

        Converts processed KPI data into template-friendly format.

        Args:
            processed_data: Output from DataProcessor.process_all_tables()

        Returns:
            Dictionary with template-ready data
        """
        template_data = {
            "department_name": self.department.name,
            "department_icon": self.department.icon,
            "date": processed_data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "date_display": self._format_date_display(processed_data.get("date")),
            "has_data": processed_data.get("has_data", False),
            "kpi_data": {}
        }

        # Process each KPI category
        kpi_categories = processed_data.get("kpi_categories", {})

        for kpi_name, kpi_info in kpi_categories.items():
            if not kpi_info.get("success"):
                continue

            kpi_data = kpi_info.get("data", [])

            # Format data based on KPI type
            if kpi_name == "Food Waste":
                template_data["kpi_data"]["foodWaste"] = KPIDataFormatter.format_food_waste(kpi_data)

            elif kpi_name == "Bio Medical Waste":
                logger.info(f"DEBUG Bio Medical Waste raw data: {kpi_data}")
                template_data["kpi_data"]["biomedicalWaste"] = KPIDataFormatter.format_bio_medical_waste(kpi_data)
                logger.info(f"DEBUG Bio Medical Waste formatted: {template_data['kpi_data']['biomedicalWaste']}")

            elif kpi_name == "Horticulture":
                template_data["kpi_data"]["treesData"] = KPIDataFormatter.format_horticulture(kpi_data)

            elif kpi_name == "Slag & GCP Dust":
                template_data["kpi_data"]["slagData"] = KPIDataFormatter.format_slag_gcp_dust(kpi_data)

            elif kpi_name == "Environment Observation":
                template_data["kpi_data"]["observations"] = KPIDataFormatter.format_environment_observation(kpi_data)

            elif kpi_name == "Environment Incident":
                template_data["kpi_data"]["incidents"] = KPIDataFormatter.format_environment_incident(kpi_data)

        return template_data

    def _format_date_display(self, date_str: Optional[str]) -> str:
        """
        Format date for display in dashboard.

        Args:
            date_str: Date string (YYYY-MM-DD)

        Returns:
            Formatted date string (e.g., "May 1, 2025")
        """
        if not date_str:
            return datetime.now().strftime("%B %d, %Y")

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%B %d, %Y")
        except:
            return date_str

    def inject_data(self, template_html: str, template_data: Dict[str, Any]) -> str:
        """
        Inject data into template HTML.

        This is the CORE method that replaces hardcoded data with real data.

        Strategy:
        1. Find JavaScript data variable declarations in template
        2. Replace with new data
        3. Update date displays
        4. Handle missing data sections

        Args:
            template_html: Template HTML string
            template_data: Prepared template data

        Returns:
            Complete HTML with injected data
        """
        import re
        html = template_html

        # Replace date in title - use regex to catch any date format
        # Matches patterns like "May 1, 2025", "August 11, 2025", etc.
        html = re.sub(
            r'(<title>.*?Dashboard - )([A-Za-z]+ \d+, \d{4})(</title>)',
            rf'\1{template_data["date_display"]}\3',
            html
        )

        # Replace department name and icon
        html = html.replace(
            "🌿 Environmental Daily Report",
            f"{template_data['department_icon']} {template_data['department_name']} Daily Report"
        )

        # Replace date in header - use regex to catch any date
        html = re.sub(
            r'(📅 )([A-Za-z]+ \d+, \d{4})( \| Balgopalpur Plant)',
            rf'\1{template_data["date_display"]}\3',
            html
        )

        # Inject JavaScript data variables
        kpi_data = template_data.get("kpi_data", {})

        # Food Waste data (inject even if empty)
        food_waste_js = JavaScriptDataGenerator.to_js_variable(
            "foodWaste",
            kpi_data.get("foodWaste", [])
        )
        html = self._replace_js_variable(html, "foodWaste", food_waste_js)

        # Bio Medical Waste data (inject even if empty)
        bio_waste_js = JavaScriptDataGenerator.to_js_variable(
            "biomedicalWaste",
            kpi_data.get("biomedicalWaste", [])
        )
        html = self._replace_js_variable(html, "biomedicalWaste", bio_waste_js)

        # Horticulture data (inject even if empty)
        horti_js = JavaScriptDataGenerator.to_js_variable(
            "horticultureData",
            kpi_data.get("treesData", [])
        )
        html = self._replace_js_variable(html, "horticultureData", horti_js)

        # Slag data (inject even if empty)
        slag_js = JavaScriptDataGenerator.to_js_variable(
            "slagData",
            kpi_data.get("slagData", {"production": 0, "slag": 0, "gcpDust": 0})
        )
        html = self._replace_js_variable(html, "slagData", slag_js)

        # Environment Incident (inject even if empty)
        incident_js = JavaScriptDataGenerator.to_js_variable(
            "environmentIncident",
            kpi_data.get("incidents", [{}])[0] if kpi_data.get("incidents") else {}
        )
        html = self._replace_js_variable(html, "environmentIncident", incident_js)

        # Environment Observation (inject even if empty)
        observation_js = JavaScriptDataGenerator.to_js_variable(
            "environmentObservation",
            kpi_data.get("observations", [{}])[0] if kpi_data.get("observations") else {}
        )
        html = self._replace_js_variable(html, "environmentObservation", observation_js)

        return html

    def _replace_js_variable(self, html: str, var_name: str, new_declaration: str) -> str:
        """
        Replace a JavaScript variable declaration in HTML.

        Finds: const varName = [...];
        Replaces with: new_declaration

        Args:
            html: HTML content
            var_name: Variable name to replace
            new_declaration: New variable declaration

        Returns:
            Updated HTML
        """
        import re

        # Pattern to match: const varName = [...anything...];
        # This handles both single-line and multi-line declarations
        pattern = rf'const\s+{var_name}\s*=\s*[\[\{{].*?[\]\}}]\s*;'

        # Try to find and replace
        if re.search(pattern, html, re.DOTALL):
            html = re.sub(pattern, new_declaration, html, flags=re.DOTALL)
            logger.info(f"Replaced JavaScript variable: {var_name}")
        else:
            logger.warning(f"Could not find JavaScript variable to replace: {var_name}")

        return html

    def generate_dashboard(self, processed_data: Dict[str, Any]) -> str:
        """
        Generate complete dashboard HTML.

        Main entry point for dashboard generation.

        Args:
            processed_data: Output from DataProcessor.process_all_tables()

        Returns:
            Complete HTML string ready to display
        """
        logger.info(
            f"Generating dashboard for {self.department.id} "
            f"on {processed_data.get('date')}"
        )

        # Load template
        template_html = self.load_template()

        # Prepare data
        template_data = self.prepare_template_data(processed_data)

        # Check if we have any data
        if not template_data["has_data"]:
            logger.warning(
                f"No data available for {self.department.id} "
                f"on {processed_data.get('date')}"
            )
            # Could inject a "No data available" message here

        # Inject data
        complete_html = self.inject_data(template_html, template_data)

        logger.info(
            f"Dashboard generated successfully for {self.department.id} "
            f"({len(complete_html)} characters)"
        )

        return complete_html


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def generate_dashboard(
    department: DepartmentDefinition,
    processed_data: Dict[str, Any]
) -> str:
    """
    Convenience function to generate dashboard.

    Args:
        department: DepartmentDefinition object
        processed_data: Processed data from DataProcessor

    Returns:
        Complete HTML string
    """
    engine = TemplateEngine(department)
    return engine.generate_dashboard(processed_data)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "TemplateEngine",
    "JavaScriptDataGenerator",
    "KPIDataFormatter",
    "generate_dashboard"
]


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test template engine with ENV department"""
    from departments_config import DEPARTMENT_ENV
    '''from data_processor_eav import DataProcessor

    print("=" * 70)
    print("TEMPLATE ENGINE TEST - ENVIRONMENT DASHBOARD")
    print("=" * 70)

    # Check if template exists
    print(f"\n1. Checking template: {DEPARTMENT_ENV.template_file}")
    if DEPARTMENT_ENV.template_exists:
        print(f"   ✅ Template found: {DEPARTMENT_ENV.template_path}")
    else:
        print(f"   ❌ Template not found: {DEPARTMENT_ENV.template_path}")
        print("   NOTE: Upload env_dashboard.html to templates/ directory")
        exit(1)

    # Process data
    test_date = "2025-08-20"
    print(f"\n2. Processing data for {test_date}...")

    processor = DataProcessor(DEPARTMENT_ENV)
    processed_data = processor.process_all_tables(test_date)

    print(f"   Has data: {processed_data['has_data']}")
    print(f"   KPI categories: {len(processed_data['kpi_categories'])}")

    # Generate dashboard
    print("\n3. Generating dashboard HTML...")

    engine = TemplateEngine(DEPARTMENT_ENV)

    try:
        dashboard_html = engine.generate_dashboard(processed_data)

        print(f"   ✅ Dashboard generated successfully!")
        print(f"   HTML length: {len(dashboard_html)} characters")

        # Save to file for inspection
        output_file = os.path.join(
            StorageConfig.DASHBOARDS_DIR,
            f"test_dashboard_{test_date}.html"
        )

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)

        print(f"\n4. Dashboard saved to: {output_file}")
        print(f"   Open in browser to view!")

        # Show data summary
        print("\n5. Data Summary:")
        for kpi, kpi_info in processed_data['kpi_categories'].items():
            if kpi_info.get('count', 0) > 0:
                print(f"   ✅ {kpi}: {kpi_info['count']} records")
            else:
                print(f"   ⚠️  {kpi}: No data")

    except Exception as e:
        print(f"   ❌ Error generating dashboard: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("✅ Template engine test complete!")'''