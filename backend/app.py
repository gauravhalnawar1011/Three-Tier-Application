import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics

# --------------------------------------------------
# Logging Configuration
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(__name__)

 

# --------------------------------------------------
# Flask App
# --------------------------------------------------

app = Flask(__name__)

# Allow requests from all origins (Demo / Lab only)
CORS(
    app,
    resources={
        r"/*": {
            "origins": "*"
        }
    },
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

metrics = PrometheusMetrics(app)


# --------------------------------------------------
# Database Connection
# --------------------------------------------------

def get_db_connection():
    """
    Returns a PostgreSQL connection.

    Raises:
        psycopg2.Error
    """

    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        sslmode=os.getenv("DB_SSLMODE", "require"),
        connect_timeout=5
    )

# --------------------------------------------------
# Health Checks
# --------------------------------------------------

@app.route("/health")
def health():
    """
    Liveness Probe

    Used by Kubernetes to determine whether
    the application process is alive.
    """

    return jsonify({
        "status": "healthy"
    }), 200


@app.route("/ready")
def ready():
    """
    Readiness Probe

    Checks PostgreSQL connectivity.
    """

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute("SELECT 1")

        return jsonify({
            "status": "ready"
        }), 200

    except Exception as e:

        logger.exception("Readiness check failed")

        return jsonify({
            "status": "not ready",
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()

# --------------------------------------------------
# Metrics
# --------------------------------------------------

@app.route("/metrics-test")
def metrics_test():

    return "metrics working"


# --------------------------------------------------
# Root Endpoint
# --------------------------------------------------

@app.route("/")
def home():

    return "Flask API with Prometheus metrics is running 🚀"


# --------------------------------------------------
# Students API
# --------------------------------------------------

@app.route("/students", methods=["POST"])
def add_student():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "error": "Invalid JSON request"
        }), 400

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO students
            (
                first_name,
                last_name,
                birth_date,
                email,
                enrolled_date
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING student_id;
            """,
            (
                data.get("first_name"),
                data.get("last_name"),
                data.get("birth_date"),
                data.get("email"),
                data.get("enrolled_date")
            )
        )

        student_id = cur.fetchone()[0]

        conn.commit()

        return jsonify({

            "message": "Student added successfully",

            "student_id": student_id

        }), 201

    except Exception as e:

        logger.exception("Unable to create student")

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


@app.route("/students", methods=["GET"])
def get_students():

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        cur.execute(
            "SELECT * FROM students;"
        )

        students = cur.fetchall()

        return jsonify(
            students
        ), 200

    except Exception as e:

        logger.exception("Unable to fetch students")

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()
@app.route("/students/<int:student_id>", methods=["PATCH"])
def update_student(student_id):

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid JSON request"
        }), 400

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            "SELECT * FROM students WHERE student_id = %s",
            (student_id,)
        )

        student = cur.fetchone()

        if not student:

            return jsonify({
                "message": "Student not found"
            }), 404

        first_name = data.get(
            "first_name",
            student["first_name"]
        )

        last_name = data.get(
            "last_name",
            student["last_name"]
        )

        email = data.get(
            "email",
            student["email"]
        )

        birth_date = data.get(
            "birth_date",
            student["birth_date"]
        )

        enrolled_date = data.get(
            "enrolled_date",
            student["enrolled_date"]
        )

        cur.execute(
            """
            UPDATE students
            SET
                first_name=%s,
                last_name=%s,
                email=%s,
                birth_date=%s,
                enrolled_date=%s
            WHERE student_id=%s
            """,
            (
                first_name,
                last_name,
                email,
                birth_date,
                enrolled_date,
                student_id
            )
        )

        conn.commit()

        return jsonify({
            "message": "Student updated successfully"
        })

    except Exception as e:

        logger.exception("Unable to update student")

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


@app.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM students WHERE student_id=%s",
            (student_id,)
        )

        if cur.fetchone() is None:

            return jsonify({
                "message": "Student not found"
            }), 404

        cur.execute(
            "DELETE FROM students WHERE student_id=%s",
            (student_id,)
        )

        conn.commit()

        return jsonify({
            "message": f"Student {student_id} deleted successfully"
        })

    except Exception as e:

        logger.exception("Unable to delete student")

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


@app.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id):

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        cur.execute(
            "SELECT * FROM students WHERE student_id=%s;",
            (student_id,)
        )

        student = cur.fetchone()

        if student:

            return jsonify(student), 200

        return jsonify({
            "message": "Student not found"
        }), 404

    except Exception as e:

        logger.exception("Unable to fetch student")

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# --------------------------------------------------
# Items API
# --------------------------------------------------

@app.route("/items", methods=["POST"])
def create_item():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "error": "Invalid JSON request"
        }), 400

    name = data.get("name")
    description = data.get("description")

    if not name:

        return jsonify({
            "error": "Name is required"
        }), 400

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO items
            (name, description)
            VALUES
            (%s, %s)
            RETURNING id;
            """,
            (name, description)
        )

        new_id = cur.fetchone()[0]

        conn.commit()

        return jsonify({
            "id": new_id,
            "name": name,
            "description": description
        }), 201

    except Exception as e:

        logger.exception("Unable to create item")

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


@app.route("/items", methods=["GET"])
def get_all_items():

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            "SELECT id,name,description FROM items;"
        )

        items = cur.fetchall()

        return jsonify([
            {
                "id": item[0],
                "name": item[1],
                "description": item[2]
            }
            for item in items
        ])

    except Exception as e:

        logger.exception("Unable to fetch  items")

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()

@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            "SELECT id, name, description FROM items WHERE id = %s;",
            (item_id,)
        )

        item = cur.fetchone()

        if item is None:

            return jsonify({
                "error": "Item not found"
            }), 404

        return jsonify({
            "id": item[0],
            "name": item[1],
            "description": item[2]
        }), 200

    except Exception as e:

        logger.exception("Unable to fetch item")

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "error": "Invalid JSON request"
        }), 400

    name = data.get("name")
    description = data.get("description")

    if not name and not description:

        return jsonify({
            "error": "At least one field (name or description) is required"
        }), 400

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            "SELECT id, name, description FROM items WHERE id = %s;",
            (item_id,)
        )

        item = cur.fetchone()

        if item is None:

            return jsonify({
                "error": "Item not found"
            }), 404

        if name is None:
            name = item[1]

        if description is None:
            description = item[2]

        cur.execute(
            """
            UPDATE items
            SET
                name = %s,
                description = %s
            WHERE id = %s;
            """,
            (
                name,
                description,
                item_id
            )
        )

        conn.commit()

        return jsonify({
            "id": item_id,
            "name": name,
            "description": description
        }), 200

    except Exception as e:

        logger.exception("Unable to update item")

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):

    conn = None
    cur = None

    try:

        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM items WHERE id = %s;",
            (item_id,)
        )

        if cur.fetchone() is None:

            return jsonify({
                "error": "Item not found"
            }), 404

        cur.execute(
            "DELETE FROM items WHERE id = %s;",
            (item_id,)
        )

        conn.commit()

        return jsonify({
            "message": f"Item with id {item_id} deleted successfully."
        }), 200

    except Exception as e:

        logger.exception("Unable to delete item")

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# --------------------------------------------------
# Application Entry Point
# --------------------------------------------------

if __name__ == "__main__":

    logger.info("Starting Flask Application...")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    )