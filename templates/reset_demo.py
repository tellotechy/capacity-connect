import sqlite3


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_db_connection():

    connection = sqlite3.connect(
        "capacity_connect.db"
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ==================================================
# RESET DEMO EMPLOYEE
# ==================================================

def reset_demo():

    connection = get_db_connection()

    try:

        # ==========================================
        # FIND DEMO EMPLOYEE
        # ==========================================

        employee = connection.execute("""
            SELECT
                id,
                name,
                email

            FROM users

            WHERE email = ?
        """, (
            "rahul@demo.com",
        )).fetchone()


        if employee is None:

            print("")
            print("❌ Demo employee not found.")
            print("Run app.py once before using reset_demo.py.")
            print("")

            connection.close()
            return


        user_id = employee["id"]


        print("")
        print("========================================")
        print("   CAPACITY CONNECT - DEMO RESET")
        print("========================================")
        print("")
        print("Employee:", employee["name"])
        print("Email:", employee["email"])
        print("")
        print("Resetting demo data...")


        # ==========================================
        # DELETE MODULE COMPLETIONS
        # ==========================================

        connection.execute("""
            DELETE FROM module_completions

            WHERE user_id = ?
        """, (
            user_id,
        ))


        # ==========================================
        # DELETE ASSESSMENT RESULTS
        # ==========================================

        connection.execute("""
            DELETE FROM assessment_results

            WHERE user_id = ?
        """, (
            user_id,
        ))


        # ==========================================
        # DELETE CERTIFICATES
        # ==========================================

        connection.execute("""
            DELETE FROM certificates

            WHERE user_id = ?
        """, (
            user_id,
        ))


        # ==========================================
        # DELETE COURSE ENROLLMENTS
        # ==========================================

        connection.execute("""
            DELETE FROM enrollments

            WHERE user_id = ?
        """, (
            user_id,
        ))


        # ==========================================
        # RESET HTML SKILL
        # ==========================================

        connection.execute("""
            UPDATE user_skills

            SET
                current_level = 75,
                required_level = 80

            WHERE user_id = ?
            AND skill_name = 'HTML'
        """, (
            user_id,
        ))


        # ==========================================
        # RESET CSS SKILL
        # ==========================================

        connection.execute("""
            UPDATE user_skills

            SET
                current_level = 60,
                required_level = 80

            WHERE user_id = ?
            AND skill_name = 'CSS'
        """, (
            user_id,
        ))


        # ==========================================
        # RESET JAVASCRIPT SKILL
        # ==========================================

        connection.execute("""
            UPDATE user_skills

            SET
                current_level = 35,
                required_level = 80

            WHERE user_id = ?
            AND skill_name = 'JavaScript'
        """, (
            user_id,
        ))


        # ==========================================
        # RESET SQL SKILL
        # ==========================================

        connection.execute("""
            UPDATE user_skills

            SET
                current_level = 55,
                required_level = 75

            WHERE user_id = ?
            AND skill_name = 'SQL'
        """, (
            user_id,
        ))


        # ==========================================
        # SAVE CHANGES
        # ==========================================

        connection.commit()


        # ==========================================
        # VERIFY RESET
        # ==========================================

        skills = connection.execute("""
            SELECT
                skill_name,
                current_level,
                required_level,

                CASE
                    WHEN required_level > current_level
                    THEN required_level - current_level
                    ELSE 0
                END AS skill_gap

            FROM user_skills

            WHERE user_id = ?

            ORDER BY
                skill_gap DESC,
                id ASC
        """, (
            user_id,
        )).fetchall()


        enrollment_count = connection.execute("""
            SELECT COUNT(*) AS total

            FROM enrollments

            WHERE user_id = ?
        """, (
            user_id,
        )).fetchone()["total"]


        certificate_count = connection.execute("""
            SELECT COUNT(*) AS total

            FROM certificates

            WHERE user_id = ?
        """, (
            user_id,
        )).fetchone()["total"]


        assessment_count = connection.execute("""
            SELECT COUNT(*) AS total

            FROM assessment_results

            WHERE user_id = ?
        """, (
            user_id,
        )).fetchone()["total"]


        module_count = connection.execute("""
            SELECT COUNT(*) AS total

            FROM module_completions

            WHERE user_id = ?
        """, (
            user_id,
        )).fetchone()["total"]


        print("")
        print("✅ Demo employee reset successfully.")
        print("")
        print("----------------------------------------")
        print("SKILL STATUS")
        print("----------------------------------------")


        for skill in skills:

            print(
                skill["skill_name"],
                ":",
                str(skill["current_level"]) + "%",
                "/",
                str(skill["required_level"]) + "%",
                "| Gap:",
                str(skill["skill_gap"]) + "%"
            )


        print("")
        print("----------------------------------------")
        print("LEARNING DATA")
        print("----------------------------------------")

        print(
            "Enrollments:",
            enrollment_count
        )

        print(
            "Completed Modules:",
            module_count
        )

        print(
            "Assessment Attempts:",
            assessment_count
        )

        print(
            "Certificates:",
            certificate_count
        )


        print("")
        print("----------------------------------------")
        print("SMART RECOMMENDATION")
        print("----------------------------------------")

        print(
            "JavaScript has the highest skill gap:"
        )

        print(
            "35% Current → 80% Required → 45% Gap"
        )

        print(
            "Recommended Course: JavaScript Core Skills"
        )


        print("")
        print("========================================")
        print("   DEMO IS READY 🚀")
        print("========================================")
        print("")


    except sqlite3.Error as error:

        connection.rollback()

        print("")
        print("❌ Database error:")
        print(error)
        print("")


    finally:

        connection.close()


# ==================================================
# RUN RESET
# ==================================================

if __name__ == "__main__":

    reset_demo()