import uuid
from collections import defaultdict

from app.core.enums import SeatStatus
from app.schemas.venues import SeatMapResponse, CategorySeatsResponse, RowResponse, SeatResponse

class SeatMapBuilder:
    @staticmethod
    def build(
        showtime_id: uuid.UUID,
        screen_type: str,
        status:str,
        pricing: list,
        seat_types: list,
        physical_seats: list,
        live_statuses: dict[str, str]
    ) -> SeatMapResponse:
        pricing_map = {p.seat_type_id: float(p.price) for p in pricing}
        seat_type_by_id = {st.id: st for st in seat_types}

        # Group physical seats by category and row
        category_rows = defaultdict(lambda: defaultdict(list))
        for seat in physical_seats:
            st = seat_type_by_id.get(seat.seat_type_id)
            if not st:
                continue
            seat_status = live_statuses.get(seat.seat_code, SeatStatus.AVAILABLE.value)
            category_rows[st][seat.row_label].append(
                SeatResponse(seat_code=seat.seat_code, status=seat_status)
            )

        # Sort and construct categories list
        categories_list = []
        # Premium categories first (descending display_order)
        sorted_categories = sorted(category_rows.keys(), key=lambda x: x.display_order, reverse=True)

        for st in sorted_categories:
            rows_list = []
            for row_label in sorted(category_rows[st].keys()):
                rows_list.append(RowResponse(row=row_label, seats=category_rows[st][row_label]))
            
            price_paise = int(pricing_map.get(st.id, 0.0) * 100)
            categories_list.append(
                CategorySeatsResponse(id=st.id, name=st.name, price_paise=price_paise, rows=rows_list)
            )

        return SeatMapResponse(
            showtime_id=showtime_id,
            screen_type=screen_type,
            status=status,
            categories=categories_list
        )
