from agentmesh.core.message import Message, Role


def test_message_to_dict_roundtrip_fields():
      msg = Message(role=Role.USER, content="hello", sender="alice")
      data = msg.to_dict()

    assert data["role"] == "user"
    assert data["content"] == "hello"
    assert data["sender"] == "alice"
    assert "id" in data and "created_at" in data
