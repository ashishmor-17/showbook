import uuid
from collections import defaultdict

from app.core.enums import SeatStatus
from app.schemas.venues import SeatMapResponse, CategorySeatsResponse, RowResponse, SeatResponse

class SeatMapBuilder:
    @staticmethod
    def build(
        showtime_id: uuid.UUID,
        screen_type: str,
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
            status = live_statuses.get(seat.seat_code, SeatStatus.AVAILABLE.value)
            category_rows[st][seat.row_label].append(
                SeatResponse(seat_code=seat.seat_code, status=status)
            )

        # Sort and construct categories list
        categories_list = []
        # Premium categories first (descending display_order)
        sorted_categories = sorted(category_rows.keys(), key=lambda x: x.display_order, reverse=True)

        for st in sorted_categories:
            rows_list = []
            # Sort rows alphabetically
            for row_label in sorted(category_rows[st].keys()):
                # Sort seats numerically by seat number
                sorted_seats = sorted(
                    category_rows[st][row_label],
                    key=lambda x: int(x.seat_code.split('-')[1]) if '-' in x.seat_code else 0
                )
                rows_list.append(RowResponse(row=row_label, seats=sorted_seats))
            
            price = pricing_map.get(st.id, 0.0)
            categories_list.append(
                CategorySeatsResponse(id=st.id, name=st.name, price=price, rows=rows_list)
            )

        return SeatMapResponse(
            showtime_id=showtime_id,
            screen_type=screen_type,
            categories=categories_list
        )
