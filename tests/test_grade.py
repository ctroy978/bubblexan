import math
import tempfile
import unittest
from pathlib import Path

import grade


class GradeTests(unittest.TestCase):
    def test_score_multiple_select_canvas_math(self):
        score, explanation = grade.score_multiple_select(2.0, 3, 2, 1)
        self.assertEqual(score, 0.67)
        self.assertIn("2 correct", explanation)
        self.assertIn("1 incorrect", explanation)

        score, _ = grade.score_multiple_select(4.0, 3, 3, 0)
        self.assertEqual(score, 4.0)

        score, _ = grade.score_multiple_select(2.0, 3, 0, 2)
        self.assertEqual(score, 0.0)

    def test_grade_responses_creates_expected_scores(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            answer_key = tmp_path / "answer_key.csv"
            answer_key.write_text(
                """Question,Correct_Answer,Points\n"""
                "Q1,b,2\n"
                "Q2,c,2\n"
                'Q3,"b,c,d",2\n'
                'Q4,"a,c",2\n'
                'Q18,"b,c,d",4\n'
            )

            report = tmp_path / "report.csv"
            report.write_text(
                """student_id,question_id,selected_answers\n"""
                "S001,Q1,b\n"
                'S001,Q2,a\n'
                'S001,Q3,"b,c"\n'
                'S001,Q4,"a,c,d"\n'
                'S001,Q18,"b,c,d"\n'
                'S002,Q1,a\n'
                'S002,Q2,c\n'
                'S002,Q3,"a"\n'
                'S002,Q4,"c"\n'
                'S002,Q18,"b,d"\n'
                'S003,Q1,b\n'
                'S003,Q2,c\n'
                'S003,Q3,"a,b,c,d"\n'
                'S003,Q4,"a,c"\n'
                'S003,Q18,"a,b,c,d"\n'
            )

            graded_df, stats_df = grade.grade_responses(report, answer_key)

            self.assertEqual(len(graded_df), 15)

            s1_q3 = graded_df[(graded_df["student_id"] == "S001") & (graded_df["question_id"] == "Q3")].iloc[0]
            self.assertTrue(math.isclose(s1_q3["score_per_question"], 1.33, rel_tol=1e-4))
            self.assertTrue(math.isclose(s1_q3["total_score"], 8.33, rel_tol=1e-4))
            self.assertTrue(math.isclose(s1_q3["percent_grade"], 69.42, rel_tol=1e-4))

            s2_total = graded_df[graded_df["student_id"] == "S002"]["total_score"].iloc[0]
            self.assertTrue(math.isclose(s2_total, 5.67, rel_tol=1e-4))

            s3_percent = graded_df[graded_df["student_id"] == "S003"]["percent_grade"].iloc[0]
            self.assertTrue(math.isclose(s3_percent, 83.33, rel_tol=1e-4))

            q3_stats = stats_df[stats_df["question_id"] == "Q3"].iloc[0]
            self.assertTrue(math.isclose(q3_stats["mean_score"], 0.89, rel_tol=1e-4))
            self.assertTrue(math.isclose(q3_stats["percent_correct"], 44.33, rel_tol=1e-4))


if __name__ == "__main__":
    unittest.main()
