import os, time, uuid, json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import boto3

CFG = dict(endpoint_url="http://localhost:4566", region_name="us-east-1",
           aws_access_key_id="test", aws_secret_access_key="test")
BUCKET, TABLE = "cloudvault-files", "cloudvault-meta"

s3 = boto3.client("s3", **CFG)
db = boto3.client("dynamodb", **CFG)
sqs = boto3.client("sqs", **CFG)
sns = boto3.client("sns", **CFG)

def setup():
    try:
        s3.create_bucket(Bucket=BUCKET)
    except Exception:
        pass
    try:
        db.create_table(
            TableName=TABLE,
            AttributeDefinitions=[{"AttributeName": "file_id", "AttributeType": "S"}],
            KeySchema=[{"AttributeName": "file_id", "KeyType": "HASH"}],
            BillingMode="PAY_PER_REQUEST")
    except Exception:
        pass
    q = sqs.create_queue(QueueName="cloudvault-events")["QueueUrl"]
    t = sns.create_topic(Name="cloudvault-alerts")["TopicArn"]
    return q, t

QUEUE_URL, TOPIC_ARN = setup()

def log_event(action, name):
    msg = json.dumps({"action": action, "file": name,
                      "time": time.strftime("%Y-%m-%d %H:%M:%S")})
    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=msg)
    sns.publish(TopicArn=TOPIC_ARN, Message=msg, Subject="CloudVault " + action)

def refresh(flt=""):
    tree.delete(*tree.get_children())
    for it in db.scan(TableName=TABLE).get("Items", []):
        name, tag = it["name"]["S"], it["tag"]["S"]
        if flt and flt.lower() not in name.lower() and flt.lower() not in tag.lower():
            continue
        tree.insert("", tk.END, iid=it["file_id"]["S"],
                    values=(name, tag, it["size"]["N"], it["uploaded"]["S"]))

def selected():
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Select", "Pehle file chuno")
        return None
    return sel[0], str(tree.item(sel[0])["values"][0])

def upload():
    path = filedialog.askopenfilename()
    if not path:
        return
    tag = simpledialog.askstring("Tag", "Tag likho (jaise resume, photo):") or "general"
    fid, name = str(uuid.uuid4()), os.path.basename(path)
    s3.upload_file(path, BUCKET, fid + "/" + name)
    db.put_item(TableName=TABLE, Item={
        "file_id": {"S": fid}, "name": {"S": name}, "tag": {"S": tag},
        "size": {"N": str(os.path.getsize(path))},
        "uploaded": {"S": time.strftime("%Y-%m-%d %H:%M:%S")}})
    log_event("UPLOAD", name)
    refresh()

def download():
    s = selected()
    if not s:
        return
    fid, name = s
    save = filedialog.asksaveasfilename(initialfile=name)
    if save:
        s3.download_file(BUCKET, fid + "/" + name, save)
        log_event("DOWNLOAD", name)
        messagebox.showinfo("Done", "Download ho gaya")

def delete():
    s = selected()
    if not s:
        return
    fid, name = s
    s3.delete_object(Bucket=BUCKET, Key=fid + "/" + name)
    db.delete_item(TableName=TABLE, Key={"file_id": {"S": fid}})
    log_event("DELETE", name)
    refresh()

def show_activity():
    win = tk.Toplevel(root)
    win.title("Activity Log")
    box = tk.Text(win, width=70, height=18)
    box.pack(padx=8, pady=8)
    res = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=10,
                              VisibilityTimeout=0)
    for m in res.get("Messages", []):
        d = json.loads(m["Body"])
        box.insert(tk.END, f'{d["time"]}  {d["action"]}  {d["file"]}\n')

root = tk.Tk()
root.title("CloudVault")
root.geometry("640x400")

top = tk.Frame(root)
top.pack(fill="x", padx=8, pady=6)
search = tk.Entry(top, width=30)
search.pack(side="left")
tk.Button(top, text="Search", command=lambda: refresh(search.get())).pack(side="left", padx=4)
tk.Button(top, text="Show all", command=lambda: refresh()).pack(side="left")

tree = ttk.Treeview(root, columns=("name", "tag", "size", "uploaded"),
                    show="headings", height=14)
for c, w in (("name", 200), ("tag", 100), ("size", 80), ("uploaded", 160)):
    tree.heading(c, text=c.title())
    tree.column(c, width=w)
tree.pack(fill="both", expand=True, padx=8)

bar = tk.Frame(root)
bar.pack(pady=8)
for text, cmd in (("Upload", upload), ("Download", download),
                  ("Delete", delete), ("Activity Log", show_activity)):
    tk.Button(bar, text=text, width=12, command=cmd).pack(side="left", padx=4)

refresh()
root.mainloop()
