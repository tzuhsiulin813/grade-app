import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import zipfile
import io
import os
import glob # 用來搜尋檔案的工具

# 設定頁面
st.set_page_config(page_title="全校排名分析系統", layout="wide")
st.title("📊 全校排名自動分析 App (多字型版)")

# --------------------------
# 側邊欄：設定區
# --------------------------
st.sidebar.header("1. 字型設定")

# 1. 自動搜尋資料夾內的所有 .ttf 和 .otf 檔案
font_files = glob.glob("*.ttf") + glob.glob("*.otf")
# 過濾掉暫存檔
font_files = [f for f in font_files if "temp" not in f]

if font_files:
    # 如果有找到字型，顯示下拉選單
    st.sidebar.success(f"📂 偵測到 {len(font_files)} 個字型檔")
    selected_font_name = st.sidebar.selectbox("請選擇要使用的字型：", font_files)
    font_path = selected_font_name
else:
    # 如果沒找到，顯示上傳框
    st.sidebar.warning("⚠️ 資料夾內找不到字型，請上傳：")
    uploaded_font = st.sidebar.file_uploader("上傳 .ttf 字型", type=["ttf", "otf"])
    if uploaded_font:
        font_path = "temp_font.ttf"
        with open(font_path, "wb") as f:
            f.write(uploaded_font.getbuffer())
    else:
        font_path = None

# --------------------------
# 2. 資料上傳與參數
# --------------------------
st.sidebar.header("2. 成績與參數")
uploaded_data = st.sidebar.file_uploader("上傳成績 CSV", type=["csv"])
total_students = st.sidebar.number_input("全校總人數 (Y軸底限)", value=300)

# --------------------------
# 主程式邏輯
# --------------------------
if font_path and uploaded_data:
    # 載入選定的字型
    font_prop = fm.FontProperties(fname=font_path)
    
    try:
        df = pd.read_csv(uploaded_data)
        
        # --- 讓使用者選擇欄位 (保持之前的功能) ---
        st.subheader("📋 資料設定")
        col1, col2 = st.columns(2)
        all_columns = df.columns.tolist()
        
        with col1:
            # 預設選第2欄當姓名
            default_name_idx = 1 if len(all_columns) > 1 else 0
            name_col = st.selectbox("誰是「姓名」欄位？", all_columns, index=default_name_idx)
            
        with col2:
            # 自動選取剩下的當成績
            default_exams = [c for c in all_columns if c != name_col and c != all_columns[0]]
            exam_cols = st.multiselect("選擇考試科目", all_columns, default=default_exams)

        st.markdown("---")

        if st.button("🚀 使用新字型生成報表"):
            if not exam_cols:
                st.error("❌ 請至少選擇一個科目！")
            else:
                progress_bar = st.progress(0)
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
                    total_count = len(df)
                    
                    for i, (idx, row) in enumerate(df.iterrows()):
                        # 更新進度
                        progress_bar.progress((i + 1) / total_count)
                        
                        name = str(row[name_col])
                        scores = row[exam_cols]
                        
                        # --- 繪圖 ---
                        fig, ax = plt.subplots(figsize=(12, 6))
                        valid_scores = pd.to_numeric(scores, errors='coerce')
                        
                        ax.plot(exam_cols, valid_scores, marker='o', linewidth=2, color='#2563eb')
                        ax.set_ylim(total_students, 1)
                        ax.grid(True, linestyle='--', alpha=0.5)
                        
                        # 使用選定的字型
                        ax.set_title(f"{name} - 校排名趨勢圖", fontproperties=font_prop, fontsize=24)
                        ax.set_xlabel("考試次別", fontproperties=font_prop, fontsize=14)
                        ax.set_ylabel("校排名", fontproperties=font_prop, fontsize=14)
                        
                        for label in ax.get_xticklabels() + ax.get_yticklabels():
                            label.set_fontproperties(font_prop)
                            
                        # 標註
                        for x, y in zip(exam_cols, valid_scores):
                            if pd.notna(y):
                                ax.annotate(str(int(y)), (x, y), xytext=(0, 10), textcoords='offset points', 
                                            ha='center', fontsize=12, fontproperties=font_prop)
                        
                        # 存檔
                        img_buffer = io.BytesIO()
                        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
                        plt.close(fig)
                        zf.writestr(f"{name}_校排名.png", img_buffer.getvalue())

                st.success(f"🎉 成功使用 {font_path} 字型生成！")
                st.download_button("📥 下載 ZIP", data=zip_buffer.getvalue(), file_name="全班成績報表.zip", mime="application/zip")

    except Exception as e:
        st.error(f"發生錯誤：{e}")
else:
    st.info("👈 請在左側確認「字型」與「成績檔」是否就緒")