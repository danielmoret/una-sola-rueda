import React, { useEffect, useContext } from "react";
import { Context } from "../store/appContext";
import { useJwt } from "react-jwt";
import { useNavigate } from "react-router-dom";
import "../../styles/user.css";
import { NewUser } from "../component/newUser";

export const User = () => {
  const { store, actions } = useContext(Context);
  const navigate = useNavigate();
  const { decodedToken, isExpired } = useJwt(store.token);

  useEffect(() => {
    if (!store.token) {
      navigate("/");
    } else if (store.role !== "raffler") {
      return;
    } else {
      navigate("/administrador/talonarios");
    }
  }, [store.token]);

  useEffect(() => {
    if (store.users && store.users.length > 0) return;
    actions.getUsers();
  }, []);

  const deleteUser = async (userId) => {
    const response = await actions.deleteUser(userId);
    if (response) {
      actions.toggleMessage("Usuario eliminado correctamente", true);
    } else {
      actions.toggleMessage("No se pudo eliminar el usuario", false);
    }
  };

  return (
    <div className="container table-user  mt-4 mb-4">
      <div className="d-flex justify-content-between">
        <h2 className="text-white">Usuarios</h2>
        <NewUser />
      </div>
      <table className="table text-white">
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Username</th>
          </tr>
        </thead>
        <tbody>
          {store.users
            .filter((user) => user.role == "raffler")
            .map((user, index) => (
              <tr key={user.id}>
                <th scope="row">{index + 1}</th>
                <td>{user.email}</td>
                <td>
                  <button
                    className="btn btn-danger"
                    onClick={() => deleteUser(user.id)}
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
};
