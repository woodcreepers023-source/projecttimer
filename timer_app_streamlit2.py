elif st.session_state.page == "instakill":
    if not st.session_state.auth:
        st.warning("You must login first.")
        if st.button("Go to Login", use_container_width=True):
            goto("login")
    else:
        render_admin_tabs(active="instakill")
        st.caption(f"✅ Admin: {st.session_state.username}")

        st.subheader("💀 InstaKill")

        # toast state (auto-hide)
        st.session_state.setdefault("ik_toast", None)

        # EXACT order you requested
        CUSTOM_BOSS_ORDER = [
            "Venatus","Viorent","Ego","Livera","Undomiel","Araneo","Lady Dalia",
            "General Aquleus","Amentis","Baron Braudmore","Wannitas","Metus","Duplican",
            "Shuliar","Gareth","Titore","Larba","Catena","Secreta","Ordo","Asta","Supore",
        ]
        order_index = {name: i for i, name in enumerate(CUSTOM_BOSS_ORDER)}
        timers_sorted = sorted(timers, key=lambda x: order_index.get(x.name, 999))

        # ONE BOX: name + button
        st.markdown("""
        <style>
          .ik-box{
            background: #ffffff;
            border: 1px solid #d1d5db;
            border-radius: 14px;
            padding: 12px;
            margin-bottom: 14px;
          }
          .ik-name{
            background: #f3f4f6;
            border: 1px solid #d1d5db;
            border-radius: 12px;
            padding: 14px 10px;
            font-weight: 800;
            letter-spacing: .18em;
            text-transform: uppercase;
            text-align: center;
            color: #111827;
            margin-bottom: 10px;
          }
          /* keep the button inside the same box style */
          .ik-box div.stButton > button{
            border-radius: 12px !important;
            border: 1px solid #cbd5e1 !important;
            background: #e5e7eb !important;
            color: #0f172a !important;
            font-weight: 700 !important;
            padding: 0.65rem 0.9rem !important;
            width: 100% !important;
          }
          .ik-box div.stButton > button:hover{
            background: #dbeafe !important;
          }
        </style>
        """, unsafe_allow_html=True)

        CARDS_PER_ROW = 8

        # toast placeholder (so it stays in one place)
        toast_slot = st.empty()

        for start in range(0, len(timers_sorted), CARDS_PER_ROW):
            row = timers_sorted[start:start + CARDS_PER_ROW]
            cols = st.columns(CARDS_PER_ROW)

            for j in range(CARDS_PER_ROW):
                with cols[j]:
                    if j >= len(row):
                        st.empty()
                        continue

                    t = row[j]

                    st.markdown("<div class='ik-box'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='ik-name'>{t.name}</div>", unsafe_allow_html=True)

                    clicked = st.button("Killed Now", key=f"ik_killed_{t.name}", use_container_width=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                    if clicked:
                        old_time_str = t.last_time.strftime("%Y-%m-%d %I:%M %p")

                        updated_last = now_manila()
                        updated_next = updated_last + timedelta(seconds=t.interval_seconds)

                        # update session timers
                        for idx, obj in enumerate(st.session_state.timers):
                            if obj.name == t.name:
                                st.session_state.timers[idx].last_time = updated_last
                                st.session_state.timers[idx].next_time = updated_next
                                break

                        # save json
                        save_boss_data([
                            (x.name, x.interval_minutes, x.last_time.strftime("%Y-%m-%d %I:%M %p"))
                            for x in st.session_state.timers
                        ])

                        # log history
                        log_edit(t.name, old_time_str, updated_last.strftime("%Y-%m-%d %I:%M %p"))

                        # toast for 2.5s
                        st.session_state.ik_toast = {
                            "msg": f"✅ {t.name} updated! Next: {updated_next.strftime('%Y-%m-%d %I:%M %p')}",
                            "ts": now_manila(),
                        }
                        st.rerun()

        # toast display + auto hide after ~2.5s
        if st.session_state.ik_toast:
            toast = st.session_state.ik_toast
            age = (now_manila() - toast["ts"]).total_seconds()

            toast_slot.success(toast["msg"])

            # keep rerunning briefly so it disappears
            st_autorefresh(interval=400, key="ik_toast_tick")

            if age >= 2.5:
                st.session_state.ik_toast = None
                st.rerun()
