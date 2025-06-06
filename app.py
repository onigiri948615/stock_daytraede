# app.py
import streamlit as st
import pandas as pd
import io
from stock_trade_visualizer import show_summary

st.set_page_config(page_title="非公式SBI証券デイトレ結果分析", layout="wide")
st.title("非公式SBI証券デイトレ結果分析")
with st.expander("CSVファイルの取得方法", expanded=True):
    st.markdown("""
        1. SBI証券にログイン
        2. 右上の口座管理をクリック
        3. 上部の取引履歴をクリック
        4. 約定日から取得したい期間を選択
        5. 照会をクリック
        6. CSVダウンロードをクリック
        7. Browserfilesをクリックし
                ダウンロードしたCSVファイルをこのページにアップロード

        注意:ファイル名はSaveFile_000001_******.csvのような形式になっているはずです。 2025年05月現在   
        ファイルサイズの上限は200MBです。上限を超える場合は期間を短くして再度ダウンロードしてください。
        
        
    """)
uploaded_file = st.file_uploader("CSVファイルをアップロード", type="csv")

if uploaded_file is not None:
    content = uploaded_file.read()

    # エンコーディングを試行錯誤で特定し、行として読み込む
    for enc in ["utf-8", "cp932", "shift_jis"]:
        try:
            lines = content.decode(enc).splitlines()
            break
        except UnicodeDecodeError:
            continue
    else:
        st.error("⚠️ 文字コードが判別できませんでした。")
        st.stop()

    # ヘッダー行の特定
    header_row_index = None
    for i, line in enumerate(lines):
        if "約定日" in line:
            header_row_index = i
            break

    if header_row_index is None:
        st.error("⚠️ '約定日' を含む行が見つかりませんでした。")
        st.stop()

    # データ読み込み
    df = pd.read_csv(io.StringIO("\n".join(lines)), skiprows=header_row_index)
    st.success(f"✅ '約定日' を含む行 {header_row_index + 1} 行目から読み込みました。")

    show_summary(df)
    with st.expander("CSVデータ", expanded=False):
        st.dataframe(df)
