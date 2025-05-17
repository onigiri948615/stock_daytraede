import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def color_profit_normalized(val, max_abs):
    try:
        val = float(val)
    except:
        return ''
    
    ratio = abs(val) / max_abs if max_abs != 0 else 0
    alpha = min(0.4, ratio)

    if val > 0:
        return f'background-color: rgba(0, 180, 0, {alpha:.2f}); color: black;'
    elif val < 0:
        return f'background-color: rgba(200, 0, 0, {alpha:.2f}); color: black;'
    else:
        return ''

def show_summary(df: pd.DataFrame):
    # 整形
    df["約定日"] = pd.to_datetime(df["約定日"], errors="coerce")
    df["受渡金額/決済損益"] = pd.to_numeric(df["受渡金額/決済損益"], errors="coerce")

    df["年月"] = df["約定日"].dt.to_period("M")
    df["日付"] = df["約定日"].dt.date
    df["勝ち"] = df["受渡金額/決済損益"] > 0
    df["負け"] = df["受渡金額/決済損益"] < 0

    df["勝ち損益のみ"] = df["受渡金額/決済損益"].where(df["勝ち"])
    df["負け損益のみ"] = df["受渡金額/決済損益"].where(df["負け"])

    # 集計
    daily = df.groupby("日付").agg(
        勝ち数=("勝ち", "sum"),
        総取引数=("勝ち", "count"),
        総損益=("受渡金額/決済損益", "sum"),
        勝率=("勝ち", lambda x: (x.sum() / len(x)) * 100),
        最大損失=("受渡金額/決済損益", "min"),
        平均利益=("勝ち損益のみ", "mean"),
        平均損失=("負け損益のみ", "mean"),
        平均損益=("受渡金額/決済損益", "mean")
    ).reset_index()

    monthly = df.groupby("年月").agg(
        勝ち数=("勝ち", "sum"),
        総取引数=("勝ち", "count"),
        総損益=("受渡金額/決済損益", "sum"),
        勝率=("勝ち", lambda x: (x.sum() / len(x)) * 100),
        最大損失=("受渡金額/決済損益", "min"),
        平均利益=("勝ち損益のみ", "mean"),
        平均損失=("負け損益のみ", "mean"),
        平均損益=("受渡金額/決済損益", "mean")
    ).reset_index()

    # 最大絶対値の取得（色付け用）
    max_daily_abs = daily["総損益"].abs().max()
    max_monthly_abs = monthly["総損益"].abs().max()

    # 表示（スタイル適用）
    st.subheader("📅 日毎のトレード成績")
    styled_daily = daily.style\
        .format({
            "総損益": "{:,.0f} 円",
            "勝率": "{:.1f} %",
            "最大損失": "{:,.0f} 円",
            "平均利益": "{:,.0f} 円",
            "平均損失": "{:,.0f} 円",
            "平均損益": "{:,.0f} 円"
        })\
        .applymap(lambda v: color_profit_normalized(v, max_daily_abs), subset=["総損益"])
    st.dataframe(styled_daily)

    st.subheader("🗓️ 月毎のトレード成績")
    styled_monthly = monthly.style\
        .format({
            "総損益": "{:,.0f} 円",
            "勝率": "{:.1f} %",
            "最大損失": "{:,.0f} 円",
            "平均利益": "{:,.0f} 円",
            "平均損失": "{:,.0f} 円",
            "平均損益": "{:,.0f} 円"
        })\
        .applymap(lambda v: color_profit_normalized(v, max_monthly_abs), subset=["総損益"])
    st.dataframe(styled_monthly)

    # 成績指標
    avg_profit = df.loc[df["勝ち"], "受渡金額/決済損益"].mean()
    avg_loss = df.loc[df["負け"], "受渡金額/決済損益"].mean()
    total_profit = df.loc[df["勝ち"], "受渡金額/決済損益"].sum()
    total_loss = df.loc[df["負け"], "受渡金額/決済損益"].sum()

    payoff_ratio = avg_profit / abs(avg_loss) if avg_loss else None
    profit_factor = total_profit / abs(total_loss) if total_loss else None

    st.subheader("📊 成績指標まとめ")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("✅ ペイオフレシオ（平均）", f"{payoff_ratio:.2f}" if payoff_ratio else "計算不可")
    with col2:
        st.metric("📈 プロフィットファクター（全体）", f"{profit_factor:.2f}" if profit_factor else "計算不可")

    st.caption("※ ペイオフレシオ：1回あたりの平均利益 ÷ 平均損失｜プロフィットファクター：全体の利益 ÷ 全体の損失")

    # グラフ
    st.subheader("📈 日毎の総損益と累積損益")
    daily["累積損益"] = daily["総損益"].cumsum()

    y_min = min(daily["総損益"].min(), daily["累積損益"].min())
    y_max = max(daily["総損益"].max(), daily["累積損益"].max())
    padding = (y_max - y_min) * 0.1
    y_range = [y_min - padding, y_max + padding]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily["日付"],
        y=daily["総損益"],
        name="日毎の損益",
        yaxis="y1"
    ))
    fig.add_trace(go.Scatter(
        x=daily["日付"],
        y=daily["累積損益"],
        mode="lines+markers",
        name="累積損益",
        yaxis="y2"
    ))
    fig.update_layout(
        xaxis_title="日付",
        yaxis=dict(
            title="日毎の損益（円）",
            range=y_range,
            tickformat=","
        ),
        yaxis2=dict(
            title="累積損益（円）",
            overlaying="y",
            side="right",
            range=y_range,
            tickformat=",",
            showgrid=False
        ),
        legend=dict(x=0.01, y=0.99),
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
