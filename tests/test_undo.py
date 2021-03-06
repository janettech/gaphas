from gaphas.aspect import Connector, ConnectionSink
from gaphas.canvas import Canvas
from gaphas.examples import Box
from gaphas.item import Line


def test_undo_on_delete_element(revert_undo, undo_fixture):
    b1 = Box()
    b2 = Box()
    line = Line()

    canvas = Canvas()
    canvas.add(b1)
    assert 2 == len(canvas.solver.constraints)

    canvas.add(b2)
    assert 4 == len(canvas.solver.constraints)

    canvas.add(line)

    sink = ConnectionSink(b1, b1.ports()[0])
    connector = Connector(line, line.handles()[0])
    connector.connect(sink)

    sink = ConnectionSink(b2, b2.ports()[0])
    connector = Connector(line, line.handles()[-1])
    connector.connect(sink)

    assert 6 == len(canvas.solver.constraints)
    assert 2 == len(list(canvas.get_connections(item=line)))

    del undo_fixture[2][:]  # Clear undo_list

    # Here disconnect is not invoked!
    canvas.remove(b2)

    assert 3 == len(canvas.solver.constraints)
    assert 1 == len(list(canvas.get_connections(item=line)))

    cinfo = canvas.get_connection(line.handles()[0])
    assert b1 == cinfo.connected

    cinfo = canvas.get_connection(line.handles()[-1])
    assert cinfo is None

    assert [] == list(canvas.solver.constraints_with_variable(line.handles()[-1].pos.x))
    assert [] == list(canvas.solver.constraints_with_variable(line.handles()[-1].pos.y))

    undo_fixture[0]()  # Call undo

    assert 6 == len(canvas.solver.constraints)
    assert 2 == len(list(canvas.get_connections(item=line)))

    cinfo = canvas.get_connection(line.handles()[0])
    assert b1 == cinfo.connected

    cinfo = canvas.get_connection(line.handles()[-1])
    assert b2 == cinfo.connected
