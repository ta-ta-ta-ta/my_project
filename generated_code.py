```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class TaskManager:
    def __init__(self):
        self.tasks = pd.DataFrame(columns=['Task', 'Due Date', 'Status'])

    def add_task(self, task, due_date):
        self.tasks = self.tasks.append({'Task': task, 'Due Date': due_date, 'Status': 'Pending'}, ignore_index=True)

    def mark_task_completed(self, task):
        self.tasks.loc[self.tasks['Task'] == task, 'Status'] = 'Completed'

    def get_pending_tasks(self):
        return self.tasks[self.tasks['Status'] == 'Pending']

    def get_overdue_tasks(self):
        current_date = datetime.now().date()
        return self.tasks[self.tasks['Due Date'] < current_date]

class ReportGenerator:
    def __init__(self, tasks_df):
        self.tasks_df = tasks_df

    def generate_report(self):
        completed_tasks = self.tasks_df[self.tasks_df['Status'] == 'Completed']
        overdue_tasks = self.tasks_df[self.tasks_df['Status'] == 'Pending' & (self.tasks_df['Due Date'] < datetime.now().date())]
        report = {
            'Total Tasks': len(self.tasks_df),
            'Completed Tasks': len(completed_tasks),
            'Pending Tasks': len(overdue_tasks),
            'Overdue Tasks': len(overdue_tasks)
        }
        return report

# Example usage
task_manager = TaskManager()
task_manager.add_task("Report generation", datetime(2023, 10, 20))
task_manager.add_task("Code review", datetime(2023, 10, 25))
task_manager.mark_task_completed("Report generation")

report_generator = ReportGenerator(task_manager.tasks)
report = report_generator.generate_report()
print(report)
```